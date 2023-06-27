# Need to first start a transaction. Extract the atomic ID from the output and save it.
# Then run this bash file.
# curl -i -u fedoraAdmin:fedoraAdmin -X POST "http://localhost:8080/fcrepo/rest/fcr:tx"

atomicid="7b3e7981-8d61-46c5-af2a-a70d67ac932c"
container="arch"

echo ""
echo "The container OCFL ID"
echo ""
echo -n "info:fedora/${container}" | sha256sum


echo ""
echo "Creating a container"
echo ""
curl -i -u fedoraAdmin:fedoraAdmin -X POST -H "Slug: ${container}" -H "Link: <http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel=\"type\"" -H "Atomic-ID:http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}" http://localhost:8080/fcrepo/rest

echo ""
echo "uploading a file"
echo ""
curl -i -u fedoraAdmin:fedoraAdmin -X POST --data-binary "./test_data/s3_logo.png" -H "Content-Disposition: attachment; filename=\"s3_logo.png\"" -H "Slug:s3_logo.png" -H "Atomic-ID:http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}" http://localhost:8080/fcrepo/rest/${container}/

echo ""
echo "Commiting the transaction"
echo ""
curl -i -u fedoraAdmin:fedoraAdmin -X PUT "http://localhost:8080/fcrepo/rest/fcr:tx/${atomicid}"


#echo ""
#echo "Create a version - we don't need to do this. All of the transactions will be contained within a version."
#echo ""
#curl -i -u fedoraAdmin:fedoraAdmin -X POST http://localhost:8080/fcrepo/rest/${container}/fcr:versions
