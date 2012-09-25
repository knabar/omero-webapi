import urllib2
import json
from urllib import urlencode, quote_plus
from cookielib import CookieJar


API = 'http://127.0.0.1:8000/webapi/mpu/'


class OmeroBucket():

    def __init__(self, bucketname, username, password, server):
        self.bucketname = bucketname
        self.username = username
        self.password = password
        self.server = server

    def initiate_multipart_upload(self, filename):
        return MultiPartUpload(self, filename, self.username, self.password, self.server)

    def call_api(self, method, filename, querydict, data=None, headers=None, cookiejar=None):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar)) #urllib2.HTTPHandler if not cookiejar else 
        request = urllib2.Request(
            '%s%s?%s' % (API, quote_plus(filename), urlencode(querydict)),
            data=data)
        request.get_method = lambda: method
        if headers:
            for key, val in headers.iteritems():
                request.add_header(key, val)
        print 'Before:', cookiejar
        response = opener.open(request)
        print 'After:', cookiejar
        return json.load(response)

    def __str__(self):
        return self.bucketname



class MultiPartUpload():

    def __init__(self, bucket, filename, username, password, server):
        self.bucket = bucket
        self.filename = filename
        self.cookiejar = CookieJar()

        response = self.bucket.call_api(
            'POST', self.filename, dict(uploads='', bucket=self.bucket),
            data=urlencode(dict(username=username, password=password, server=server)),
            cookiejar=self.cookiejar)
        self.upload_id = response.get('uploadId')
        self.valid = response.get('bad', 'false') != 'true'

    def upload_part_from_file(self, f, part):
        if not self.valid:
            return False
        response = bucket.call_api(
            'PUT', self.filename, dict(uploadId=self.upload_id, partNumber=part),
            data=f.read(),
            cookiejar=self.cookiejar)
        self.valid = response.get('bad', 'false') != 'true'

    def complete_upload(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'POST', self.filename, dict(uploadId=self.upload_id),
            cookiejar=self.cookiejar)
        self.valid = response.get('bad', 'false') != 'true'

    def cancel_upload(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'DELETE', self.filename, dict(uploadId=self.upload_id),
            cookiejar=self.cookiejar)
        self.valid = response.get('bad', 'false') != 'true'

    def get_parts(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'GET', self.filename, dict(uploadId=self.upload_id),
            cookiejar=self.cookiejar)
        return response['parts']



if __name__ == '__main__':

    from StringIO import StringIO

    bucket = OmeroBucket('test', 'andreas', 'omero', 1)
    mpu = bucket.initiate_multipart_upload('test.txt')
    print 'Initialized: %s' % mpu.valid
    print mpu.upload_part_from_file(StringIO('This is a '), 1)
    print mpu.upload_part_from_file(StringIO('Test'), 2)
    print mpu.get_parts()
    print mpu.complete_upload()
    print mpu.valid

