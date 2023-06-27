import os
import http.client
import mimetypes
# import rdflib
import hashlib
import base64
from os import environ as env
# from dotenv import load_dotenv
from distutils.util import strtobool
import urllib.request
from shutil import copyfileobj

class FedoraApi:
    def __init__(self):
        # load_dotenv()
        self.host = env['FEDORA_HOST']
        self.port = env['FEDORA_PORT']
        self.username = env['FEDORA_USERNAME']
        self.password = env['FEDORA_PASSWORD']
        self.base_url = env['FEDORA_BASE_URL']
        self.use_https = bool(strtobool(env.get('FEDORA_USE_HTTPS', 'False')))
        self.ocfl_root = env['OCFL_ROOT']
        if not self.base_url.endswith("/"):
            self.base_url = self.base_url + "/"
        b64 = base64.b64encode(f"{self.username}:{self.password}".encode("ascii")).decode()
        self.auth = f"Basic {b64}"
        return

    def create_transaction(self):
        # curl -i -u fedoraAdmin:fedoraAdmin -X POST "http://localhost:8080/fcrepo/rest/fcr:tx"
        myURL = self.base_url + "fcr:tx"
        result = self._http_request(method="POST", url=myURL, payload="", headers={})
        return result

    def keep_transaction_alive(self, atomic_id):
        # curl -i -X POST "http://localhost:8080/rest/fcr:tx/ce4bb2bf-8ced-4c7d-b281-f2132e3064bb"
        if not atomic_id:
            result = {'msg': "No atomic id id given. Returning.", 'status': False}
            return result
        myURL = atomic_id
        result = self._http_request(method="POST", url=myURL, payload="", headers={})
        return result

    def commit_transaction(self, atomic_id):
        # curl -i -u fedoraAdmin:fedoraAdmin -X PUT "http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}"
        if not atomic_id:
            result = {'msg': "No atomic id id given. Returning.", 'status': False}
            return result
        myURL = atomic_id
        result = self._http_request(method="PUT", url=myURL, payload="", headers={})
        return result

    def create_container(self, container_id=None, archival_group=True, atomic_id=None):
        # curl -i -u fedoraAdmin:fedoraAdmin -X POST -H "Slug: ${container}"
        # -H "Link: <http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel=\"type\""
        # -H "Atomic-ID:http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}" http://localhost:8080/fcrepo/rest
        if not container_id:
            result = {'msg': "No container id given. Returning.", 'status': False}
            return result
        headers = {"Slug": container_id}
        if archival_group:
            # Container of type archival group
            headers["Link"] = '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"'
        if atomic_id:
            # Container is created within a transaction
            headers["Atomic-ID"] = atomic_id
        myURL = self.base_url
        result = self._http_request(method="POST", url=myURL, payload="", headers=headers)
        return result

    def create_new_version(self, container_id):
        # curl -i -u fedoraAdmin:fedoraAdmin -X POST http://localhost:8080/fcrepo/rest/${container}/fcr:versions
        if not container_id:
            result = {'msg': "No container id given. Returning.", 'status': False}
            return result
        myURL = self.base_url + container_id + "/fcr:versions"
        result = self._http_request(method="POST", url=myURL, payload="", headers={})
        return result

    def get_information(self, container_id=None):
        # TODO: This method is not working with http client. The body is empty.
        headers = {"Accept": "text/turtle"}
        myURL = self.base_url + container_id
        result = self._http_request(method="GET", url=myURL, payload="", headers=headers)
        attributes = {}
        body = result['body']
        if body:
            g = rdflib.Graph()
            g.parse(data=body, format="turtle")
            for s, p, o in g.triples((None, None, None)):
                if "fedora.info" in p:
                    prop = p.split("#")[-1]
                    attributes[prop] = o.value
        return attributes

    def post_file(self, container_id, file_path, file_location=None, atomic_id=None, mime_type=None, sha1=None,
                  sha256=None, sha512=None, calculate_digest=False):
        # curl -i -u fedoraAdmin:fedoraAdmin -X POST --data-binary "./test_data/logo.png"
        # -H "Content-Disposition: attachment; filename=\"logo.png\"" -H "Slug:logo.png"
        # -H "Atomic-ID:http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}" http://localhost:8080/fcrepo/rest/${container}/
        return self.add_file("POST", container_id, file_path, file_location=file_location, atomic_id=atomic_id,
                             mime_type=mime_type, sha1=sha1, sha256=sha256, sha512=sha512,
                             calculate_digest=calculate_digest)

    def get_data(self, url, dir):
        res = self.get_list_of_files(url)
        if isinstance(res, dict):
            return res

        result = res[0]
        filesToDownload = res[1]

        for fFile in filesToDownload:
            of = fFile.split("/")[-1]
            res = self._download_file(url=filesToDownload[0], outFile=of, outDir=dir)
            result["status"] = res
        return result

    def get_list_of_files(self, url):
        # curl  -i -u ora:orapass -H "Accept: text/turtle" -H "Accept-Datetime: Wed, 29 Aug 2018 15:47:50 GMT"
        #    https://ora4-qa-dps-witness.bodleian.ox.ac.uk:8443/fcrepo/rest/e238c36b-b871-4757-99d5-eefe0378e426
        headers = {
            "Accept": "text/turtle",
            "Accept-Datetime": "Wed, 29 Aug 2018 15:47:50 GMT", # A suitable date in the past
        }
        result = self._get_url(headers=headers, url=url)
        if not result["status"]:
            print(f"URL not found : {url}")
            return result

        # curl  -i -u ora:orapass -H "Accept: text/turtle"
        #  https://ora4-qa-dps-witness.bodleian.ox.ac.uk:8443/fcrepo/rest/e238c36b-b871-4757-99d5-eefe0378e426/fcr:versions/20230202084745
        result = self._get_url(headers=headers, url=result["location"])
        if not result["status"]:
            print(f"URL not found : {url}")
            return result
        filesToDownload = []
        for line in result['body'].decode().split("\n"):
            if line.strip().startswith("ldp:contains"):
                filesToDownload.append(line.split()[1][1:-1])
        return (result, filesToDownload)

    def update_file(self, url, file_path):
        # curl -v -i -u ora:orapass -X PUT --upload-file test_data/binary.bin
        #     -H"Content-Type: application/octet-stream" -H"digest: sha=edca4d0422d3101a40d7208c700a8ddf4db06f56"
        #     https://ora4-qa-dps-witness.bodleian.ox.ac.uk:8443/fcrepo/rest/45cc8c53-d78c-4d88-87d1-40828571b563/binary_1.bin
        if not os.path.exists(file_path):
            # return FileNotFoundError(file_path)
            result = {'msg': f"{file_path} does not exist", 'status': False}
            return result

        mime_type = self._get_mime_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_name = os.path.basename(file_path)

        link = [
            f"<file://{file_path}>",
            'rel="http://fedora.info/definitions/fcrepo#ExternalContent\"',
            'handling="copy"',
            f"type=\"{mime_type}\""
        ]

        headers = {
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Type": mime_type,
            "Link": "; ".join(link)
        }

        with open(file_path, "rb") as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
        headers["digest"] = f"sha={sha1}"

        result = self._http_request(method="PUT", url=url, payload="", headers=headers)
        return result


    def _download_file(self, url, outFile="", outDir=""):
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"{self.auth}")
        res = urllib.request.urlopen(request)
        if not outDir.endswith("/"):
            outDir = outDir + "/"
        oFile = outDir + outFile
        f = open(oFile, "wb")
        continueReading = True
        while continueReading:
            zz = res.read(5 * 1024 * 1024) # Read 5MB chunks
            if len(zz) > 0:
                f.write(zz)
            else:
                continueReading = False
        f.close()
        return True

    def _get_url(self, headers, url):
        result = self._http_request(method="GET", url=url, payload="", headers=headers)
        return result

    def put_file(self, container_id, file_path, file_location=None, atomic_id=None, mime_type=None, sha1=None,
                 sha256=None, sha512=None, calculate_digest=False):
        # curl -X PUT --upload-file image.jpg -H"Content-Type: image/jpeg"
        #      -H"digest: sha=cb1a576f22e8e3e110611b616e3e2f5ce9bdb941" "http://localhost:8080/rest/new/image"
        return self.add_file("PUT", container_id, file_path, file_location=file_location, atomic_id=atomic_id,
                             mime_type=mime_type, sha1=sha1, sha256=sha256, sha512=sha512,
                             calculate_digest=calculate_digest)

    def add_external_file(self, method, container_id, local_file_path, server_file_path, file_location=None,
                          atomic_id=None, mime_type=None, sha1=None, sha256=None, sha512=None, calculate_digest=False):
        #curl -i -H"Link: <file:///data/shared_data/largeBinary.bin>; rel=\"http://fedora.info/definitions/fcrepo#ExternalContent\";
        # handling=\"copy\"; type=\"application/octet-stream\"" -H"SLUG: largeBinary"
        # -XPOST -u fedoraAdmin:fedoraAdmin http://localhost:8080/fcrepo/rest/7516aef5-aed7-4a92-aa27-4467028c83aa/

        if not container_id:
            result = {'msg': "No container id given. Returning.", 'status': False}
            return result
        if not mime_type:
            mime_type = self._get_mime_type(local_file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
        file_name = os.path.basename(local_file_path)
        link = [
            f"<file://{server_file_path}>",
            'rel="http://fedora.info/definitions/fcrepo#ExternalContent\"',
            'handling="copy"',
            f"type=\"{mime_type}\""
        ]
        headers = {
            "Link": "; ".join(link)
        }
        if method == 'POST':
            # Add file name or location in the Slug header for POST
            if file_location:
                headers["Slug"] = file_location
            else:
                headers["Slug"] = file_name
        if atomic_id:
            # Container is created within a transaction
            headers["Atomic-ID"] = atomic_id

        if sha1:
            headers["digest"] = f"sha={sha1}"
        elif sha256:
            headers["digest"] = f"sha-256={sha256}"
        elif sha512:
            headers["digest"] = f"sha-512={sha512}"

        myURL = self.base_url + container_id
        if method == 'PUT':
            # Add file name or location in the URL for PUT
            if file_location:
                myURL = myURL + '/' + file_location
            else:
                myURL = myURL + '/' + file_name

        if calculate_digest:
            with open(local_file_path, "rb") as f:
                sha512 = hashlib.sha512(f.read()).hexdigest()
                headers["digest"] = f"sha-512={sha512}"

        result = self._http_request(method=method, url=myURL, payload="", headers=headers)
        return result

    def add_file(self, method, container_id, file_path, file_location=None, atomic_id=None, mime_type=None, sha1=None,
                 sha256=None, sha512=None, calculate_digest=False):
        if not container_id:
            result = {'msg': "No container id given. Returning.", 'status': False}
            return result
        if not os.path.exists(file_path):
            # return FileNotFoundError(file_path)
            result = {'msg': f"{file_path} does not exist", 'status': False}
            return result
        if not mime_type:
            mime_type = self._get_mime_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
        file_name = os.path.basename(file_path)
        headers = {
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Type": mime_type
        }
        if method == 'POST':
            # Add file name or location in the Slug header for POST
            if file_location:
                headers["Slug"] = file_location
            else:
                headers["Slug"] = file_name
        if atomic_id:
            # Container is created within a transaction
            headers["Atomic-ID"] = atomic_id

        if sha1:
            headers["digest"] = f"sha={sha1}"
        elif sha256:
            headers["digest"] = f"sha-256={sha256}"
        elif sha512:
            headers["digest"] = f"sha-512={sha512}"

        myURL = self.base_url + container_id
        if method == 'PUT':
            # Add file name or location in the URL for PUT
            if file_location:
                myURL = myURL + '/' + file_location
            else:
                myURL = myURL + '/' + file_name

        with open(file_path, "rb") as f:
            if calculate_digest:
                sha512 = hashlib.sha512(f.read()).hexdigest()
                headers["digest"] = f"sha-512={sha512}"
            result = self._http_request(method=method, url=myURL, payload=f.read(), headers=headers)
        return result

    def get_ocfl_object_path(self, container_id):
        container = f"info:fedora/{container_id}"
        csha = hashlib.sha256(container.encode("utf-8")).hexdigest()
        cpath = os.path.join(self.ocfl_root, csha[0:3], csha[3:6], csha[6:9], csha)
        return cpath

    def _get_mime_type(self, file_path):
        if not os.path.exists(file_path):
            return FileNotFoundError(file_path)
        mt = mimetypes.guess_type(file_path)
        if mt:
            return mt[0]
        else:
            return None

    def _http_request(self, method="GET", url="", payload="", headers={}):
        headers["Authorization"] = self.auth
        http.client.HTTPConnection._http_vsn = 10
        http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'
        if self.use_https:
            conn = http.client.HTTPSConnection(self.host, self.port)
        else:
            conn = http.client.HTTPConnection(self.host, self.port)
        conn.request(method, url, payload, headers)
        res = conn.getresponse()
        # Return a sensible dictionary
        result = {'status': False, 'msg': res.reason, 'status_code': res.status, 'body': res.read()}
        if 200 <= res.status < 400:
            result['status'] = True
            result['location'] = res.getheader("Location", "")
            result['link'] = self._get_location_from_link(res)
        else:
            print(f"Error getting information : {res.status} {url}")
        # Close should happen only after the data has been read ...
        conn.close()
        return result

    def _get_location_from_link(self, res):
        # Extract the location from headers for the original Link
        location = ""
        for j in res.getheader("Link", "").split(","):
            if "original" in j:
                location = j.split(";")[0].strip()[1:-1]
        return location

