# guarantee-token-server
Guarantee Token Main Server - for Capstone project


## What is this?

This is an main server implementation that uses Guarantee Token - a Solidity contract to store Product Information and Guarantee(Warranty) information inside NFT.


## How it works
<img width="817" alt="basic_structure" src="https://user-images.githubusercontent.com/27392567/172793224-e8b5bdd2-cb2f-4560-abf0-fc8814494709.png">

Basically, the app cannot just connect with the blockchain network since we need to login information too. 
So, there is a main server that communicates with the app with API requests.
When the main server receives API requests, it converts certain commands such as mint or transfer to RPC request and send it to our private blockchain server.


**- The full scenario -**


<img width="884" alt="structure_with_scenario" src="https://user-images.githubusercontent.com/27392567/172794251-795d930f-e469-415c-83a4-a022ef73c89e.png">



## The Capstone Fair for our school

![Capstone Picture](https://user-images.githubusercontent.com/27392567/172794929-e96807a9-a09a-4b0e-8114-8b940f05b4fc.jpg)

The Capstone Fair was held in 8th June, 2022.



## Screenshots


![screenshots](https://user-images.githubusercontent.com/27392567/172796876-e5935f06-5d47-4059-9b61-e7488c02da34.png)



## Other Links

[Android App Repository](https://github.com/Taewan-P/guarantee-token-android-app) - Kotlin


[Solidity Contract Repository](https://github.com/Taewan-P/guarantee-token) - Solidity, Go Ethereum(Geth), Truffle


[iOS App Repository](https://github.com/PrismSpirit/GuaranteeWallet-iOS-app) - Swift 5
