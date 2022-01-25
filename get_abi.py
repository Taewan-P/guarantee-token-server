import json

truffleFile = json.load(open('./build/contracts/GuaranteeToken.json'))
ABI = truffleFile['abi']

print(json.dumps(ABI))
