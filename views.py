from __future__ import with_statement

import os
import shutil
import tempfile
import logging
import time
import settings
import traceback
from uuid import uuid4 as uuid

import django.views.generic
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import simplejson


logger = logging.getLogger(__name__)


def chunk_copy(source, target):
    chunk_size = getattr(settings, 'MPU_CHUNK_SIZE', 64 * 1024)
    while True:
        chunk = source.read(chunk_size)
        if not chunk:
            break
        target.write(chunk)

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

def get_temp_path(uploadId=None):
    temp_dir = getattr(settings, 'MPU_TEMP_DIR', tempfile.gettempdir())
    if not uploadId:
        return os.path.join(temp_dir, 'mpu_uploads')
    else:
        return os.path.join(temp_dir, 'mpu_uploads', uploadId)


def _delete_upload(objectname):
    shutil.rmtree(os.path.dirname(objectname), ignore_errors=True)


# TODO: check access controls, etc.


def process_request(require_uploadId):
    def decorate_method(method):
        def decorated(self, request, objectname):
            
            if os.path.basename(objectname) != objectname:
                return HttpResponseForbidden()
            uploadId = request.GET.get('uploadId')
            if uploadId:
                path = get_temp_path(uploadId)
                objectname = os.path.join(path, objectname)
                if not os.path.exists(objectname):
                    return HttpResponseForbidden()
                touch(os.path.join(path, objectname))
            elif require_uploadId:
                return HttpResponseForbidden()
            
            try:
                rdict = {'bad': 'false'}
                rdict.update(method(self, request, objectname))
            except Exception, ex:
                logger.error(traceback.format_exc())
                rdict = {'bad': 'true', 'errs': str(ex)}
            
            json = simplejson.dumps(rdict, ensure_ascii=False)
            return HttpResponse(json, mimetype='application/javascript')
        return decorated
    return decorate_method


class MultiPartUpload(django.views.generic.View):

    @process_request(require_uploadId=True)
    def get(self, request, objectname):
        rdict = {}
        if objectname:
            rdict['parts'] = self._get_parts(objectname)
        return rdict

    @process_request(require_uploadId=False)
    def post(self, request, objectname):
        rdict = {}
        if request.GET.has_key('uploads'):
            rdict['uploadId'] = self._initiate_upload(objectname)
        else:
            self._complete_upload(objectname)
        return rdict
    
    @process_request(require_uploadId=True)
    def put(self, request, objectname):
        rdict = {}
        try:
            partNumber = int(request.GET.get('partNumber'))
        except ValueError:
            partNumber = 0
        if partNumber < 1 or partNumber > 10000:
            raise ValueError('Part number must be between 1 and 10000')
        with file('%s.%05d' % (objectname, partNumber), 'wb') as part:
            chunk_copy(request, part)
        return rdict

    @process_request(require_uploadId=True)
    def delete(self, request, objectname):
        rdict = {}
        self._delete_upload(objectname)
        return rdict

    def _initiate_upload(self, objectname):
        uploadId = str(uuid())
        path = get_temp_path(uploadId)
        os.makedirs(path)
        touch(os.path.join(path, objectname))
        return uploadId
    
    def _get_parts(self, objectname):
        filename = os.path.basename(objectname) + '.'
        return sorted(part for part in os.listdir(os.path.dirname(objectname))
                      if part.startswith(filename))
    
    def _complete_upload(self, objectname):
        parts = self._get_parts(objectname)
        if len(parts) < 1 or len(parts) != int(parts[-1][-5:]):
            raise Exception("Missing parts in multi-part upload")
        with file(objectname, 'wb') as target:
            for part in parts:
                with file(os.path.join(os.path.dirname(objectname), part)) as source:
                    chunk_copy(source, target)
        # TODO: move file to where it needs to go
        _delete_upload(objectname)


def clean_incomplete_mpus(request):
    now = time.time()
    rdict = dict()
    path = get_temp_path()
    for upload in os.listdir(path):
        p = os.path.join(path, upload)
        last_change = None
        master = None
        if os.path.isdir(p):
            files = sorted(os.listdir(p), key=len)
            if files:
                master = os.path.join(p, files[0])
                last_change = now - os.path.getatime(master)
        rdict[upload] = last_change
        if last_change > getattr(settings, 'MPU_TIMEOUT', 60 * 60):
            _delete_upload(master)
    json = simplejson.dumps(rdict, ensure_ascii=False)
    return HttpResponse(json, mimetype='application/javascript')
    