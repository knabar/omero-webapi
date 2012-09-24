import urllib2
import json
from urllib import urlencode, quote_plus


API = 'http://127.0.0.1:8000/webapi/mpu/'


class OmeroBucket():

    def __init__(self, bucketname):
        self.bucketname = bucketname

    def initiate_multipart_upload(self, filename):
        return MultiPartUpload(self, filename)

    def call_api(self, method, filename, querydict, data=None, headers=None):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(
            '%s%s?%s' % (API, quote_plus(filename), urlencode(querydict)),
            data=data)
        request.get_method = lambda: method
        if headers:
            for key, val in headers.iteritems():
                request.add_header(key, val)
        response = opener.open(request)
        return json.load(response)

    def __str__(self):
        return self.bucketname



class MultiPartUpload():

    def __init__(self, bucket, filename):
        self.bucket = bucket
        self.filename = filename

        response = self.bucket.call_api(
            'POST', self.filename, dict(uploads='', bucket=self.bucket))
        self.upload_id = response.get('uploadId')
        self.valid = response.get('bad', 'false') != 'true'

    def upload_part_from_file(self, f, part):
        if not self.valid:
            return False
        response = bucket.call_api(
            'PUT', self.filename, dict(uploadId=self.upload_id, partNumber=part),
            data=f.read())
        self.valid = response.get('bad', 'false') != 'true'

    def complete_upload(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'POST', self.filename, dict(uploadId=self.upload_id))
        self.valid = response.get('bad', 'false') != 'true'

    def cancel_upload(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'DELETE', self.filename, dict(uploadId=self.upload_id))
        self.valid = response.get('bad', 'false') != 'true'

    def get_parts(self):
        if not self.valid:
            return False
        response = bucket.call_api(
            'GET', self.filename, dict(uploadId=self.upload_id))
        return response['parts']



if __name__ == '__main__':

    from StringIO import StringIO

    bucket = OmeroBucket('test')
    mpu = bucket.initiate_multipart_upload('test.txt')
    mpu.upload_part_from_file(StringIO('This is a '), 1)
    mpu.upload_part_from_file(StringIO('Test'), 2)
    print mpu.get_parts()
    mpu.complete_upload()
    print mpu.valid

