import requests
import json

# change the server and port to match your environment
url     = "http://<server>:<port>/inject"
headers = {'Content-type': 'application/json'}

# read the list of payloads from file
with open('payload-list.txt', 'r') as f:
    payloads = f.read().splitlines()

# loop through each payload and send a request for each one
for payload in payloads:

    # example GraphQL request to inject payload
    graphql_query = '''
        query {
            user(id: "'''+{payload}+'''}") {
                name
            }
        }
    '''
    
    request_body = { 'inject_request': graphql_query }
    response     = requests.post(url, data=json.dumps(request_body), headers=headers)

    if response.status_code == 200:
        print("Payload: " + payload + " was injected successfully!")
        break
    else:
        print(".", end="")