#!/bin/sh

sed -i 's/%ABI_INFO%/'$ABI_INFO'/g' app.yaml
sed -i 's/%CONTRACT_ADDRESS%/'$CONTRACT_ADDRESS'/g' app.yaml
sed -i 's/%DB_INFO%/'$DB_INFO'/g' app.yaml
sed -i 's/%PRIVATE_KEY%/'$PRIVATE_KEY'/g' app.yaml
sed -i 's/%PUBLIC_KEY%/'$PUBLIC_KEY'/g' app.yaml
sed -i 's/%SERVER_ADDRESS%/'$SERVER_ADDRESS'/g' app.yaml