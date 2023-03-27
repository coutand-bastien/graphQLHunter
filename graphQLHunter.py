__author__              = 'couttcoutt'
__date__                = '29.01.23'
__version__             = '1.0.0'
__license__             = 'MIT'


import requests
from termcolor import colored
from datetime import datetime
from fastapi import FastAPI, Request, Body
import uvicorn
import json
import os


URL           = ''
AUTHORIZATION = ''
QL_HEADERS    = {'Content-Type': 'application/json'}

app = FastAPI()

####################################################################################
#### SERVER ROUTES 
####################################################################################
@app.post('/inject')
async def intercept_request(request: Request, inject_request: str = Body(...)):
    '''
    Function that intercepts the request and injects the payload.
     
    Parameters:
        request (Request): The request object.
        inject_request (str): The GraphQL request to inject the payload into.

    Returns:
        response (Response): The response object.
    '''
    response = requests.post(URL, json={'query': inject_request}, headers=QL_HEADERS)

    try:
        data = json.loads(response.text)

        if 'errors' in data:
            print(f'{colored("[-] Bad request :" + json.dumps(data["errors"], indent=4), "red")}')
        else:
            print(f'{colored(json.dumps(data, indent=4), "blue")}')

    except Exception as e:
        print(colored('[-] Bad request !', 'red'))

    return response


def title():
    '''
    This function prints the title of the program.
    '''
    print('''\n
                                  ______                 __    ____    __ 
                                 / ____/________ _____  / /_  / __ \\  / / 
                                / / __/ ___/ __ `/ __ \\/ __ \\/ / / / / /  
                               / /_/ / /  / /_/ / /_/ / / / / /_/ / / /___
                               \\____/_/   \\__,_/ .___/_/ /_/\\___\\_\\/_____/
                                              /_/ 
                                   __  __            __           
                                  / / / /_  ______  / /____  _____
                                 / /_/ / / / / __ \\/ __/ _ \\/ ___/
                                / __  / /_/ / / / / /_/  __/ /    
                               /_/ /_/\\__,_/_/ /_/\\__/\\___/_/     
          \n''')


def show_help():
    '''
    This function prints the help message.
    '''
    print('''[options]

        Options:
        h, help            show this help message and exit
        p, proxy           set proxy (setup the endpoint graphQL before)
        bf, bruteforce     bruteforce url to find graphql endpoint
        u, url             test an user url
        i, intro           perform an introspection
        <query>            perform query to the graphQL endpoint
        exit               exit the program
    ''')


def test_QL_url(url):
    '''
    test_QL_url() is a function that tests the validity of a GraphQL endpoint.
    It sends a query to the specified URL and checks if the response status code is 200, 401 or 403.
    This function returns a boolean indicating if the URL is a valid GraphQL endpoint or not.

    Parameters:
        url (str): The URL to test.

    Returns:
        True if the URL is a valid GraphQL endpoint, False otherwise.
    '''
    query   = 'query {__schema{types{name,fields{name}}}}'

    if (AUTHORIZATION): QL_HEADERS['Authorization'] = AUTHORIZATION
    
    try:
        response = requests.post(url, json={'query': query}, headers=QL_HEADERS)
        return response.status_code in [200, 401, 403] 

    except requests.exceptions.RequestException:
        return False
        

def brute_force_QL_url(url):
    '''
    Test a list of directories by appending them to a base URL and checking if they return a 200 status code.
    The list of directories is read from a text file called 'graphQLUrl.txt'

    Parameters:
        url (str): The base URL to test.

    Returns:
        None if no valid directory is found, otherwise it returns the valid URL.
    '''
    separator = '/' if not url.endswith('/') else '' # for making a good url at the end

    try:
        with open('graphQLUrl.txt') as f:
            directories = f.readlines()

    except FileNotFoundError:
        print(colored('[-] graphQLUrl.txt not found', 'red'))
        return

    directories = [x.strip() for x in directories]

    res = ''

    for directory in directories:
        res = url + separator + directory

        if test_QL_url(res):
            break

    return res


def parse_json_ql_introspection(response):
    '''
    This function parses the JSON response of a GraphQL introspection query.

    Parameters:
        response (str): The JSON response of the introspection query.

    Returns:
        None if the response is not a valid JSON, otherwise it returns a list of GraphQL types.
    '''
    try:
        json_file = json.loads(response)
    except json.decoder.JSONDecodeError:
        return None 

    for _, types in enumerate(json_file['data']['__schema']['types']):
        if '__' not in types['name'] and '_' not in types['name']:
            if types['kind'] == 'OBJECT':
                print(f'\n- TYPE {types["name"]}')

                for field in types['fields']:
                    # types of the object
                    if not field['type']['ofType']:
                        field_type = field['type']['name']
                    else:
                        if field['type']['ofType']['kind'] == 'LIST':

                            if field["type"]["ofType"]["ofType"]["ofType"]:
                                field_type = f'LIST[{field["type"]["ofType"]["ofType"]["ofType"]["name"]}]'
                            else:
                                field_type = field["type"]["ofType"]["ofType"]["name"]
                        else:
                            field_type = field['type']['ofType']['name']

                    field_arg = '' # reset arg fiels

                    # if detect args ==> mutation
                    if field['args']:
                        for arg in field['args']:
                            if arg['type']['kind'] == 'LIST':
                                arg_type = f'LIST[{arg["type"]["ofType"]["name"]}]'
                            else:
                                arg_type = arg['type']['name']

                            field_arg += f'{arg["name"]}: {colored(arg_type, "magenta")}, '

                    field_arg = field_arg[:len(field_arg)-2] # del the last ', '
                    print(f'\t{colored(field["name"], "green")}{"("+field_arg+")" if field_arg else ""}  ~> {colored(field_type, "magenta")}')

            elif types['kind'] == 'INPUT_OBJECT':
                print(f'\n- INPUT {types["name"]}')

                for inputfield in types['inputFields']:
                    if inputfield['type']['kind'] == 'LIST':
                        field_type = f'LIST[{inputfield["type"]["ofType"]["name"]}]'
                    else:
                        field_type = inputfield['type']['name']

                    print(f'\t{colored(inputfield["name"], "green")} ~> {colored(field_type, "magenta")}')
                

def ql_introspection():
    '''
    This function performs an introspection on the GraphQL endpoint.
    '''
    query   = 'query {__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description locations args{...InputValue}}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name}}}}}}}}'
    
    # create log file for introspection
    try:
        os.makedirs('./var/log/', exist_ok=True)
        file = open('./var/log/introspection_'+str(datetime.now())+'.txt', 'w')
    except Exception as e:
        print(os.strerror(e.errno))
       
    try:
        response = requests.post(URL, json={'query': query}, headers=QL_HEADERS)

        if response.status_code == 200:
            print(colored('OK', 'blue'))

            json.dump(response.json(), file) # save json  in file
            parse_json_ql_introspection(response.text) # display user response
        else:
            print(colored('NOP', 'red'))
            print(colored(f'[-] Error during introspection request (status code = {response.status_code}) !', 'red'))

        return response.status_code == 200

    except requests.exceptions.RequestException:
        return False


if __name__ == '__main__':
    title()
    show_help()

    valid_url = False

    while (1):
        user_input = input(colored('GQLHunter> ', 'yellow'))

        ####################################################################################
        #### URL (set url and authorization header))
        ####################################################################################
        if user_input.lower() == 'u' or user_input.lower() == 'url':
            valid_url = False # reset to false
            
            URL           = input(colored('GQLHunter ~ URL> ', 'yellow'))
            AUTHORIZATION = input(f'{colored("Authorization (empty if none)", "blue")}\n{colored("GQLHunter ~ URL ~ AUTHORIZATION> ", "yellow")}')
            
            if URL and test_QL_url(URL):
                print(colored('[+] Valid GraphQL endpoint.', 'blue'))
                print(colored('[INFO] Introspection request ... ', 'blue'), end='')
                
                ql_introspection()
                valid_url = True
            else:
                print(colored('[-] Invalid URL.', 'red'))
                
        ####################################################################################
        #### BRUTEFORCE (bruteforce url to find graphql endpoint)
        ####################################################################################
        elif user_input.lower() == 'bf' or user_input.lower() == 'bruteforce':
            print(colored('[INFO] Enter a base URL to test : ', 'blue'))
            URL = input(colored('GQLHunter ~ BF> ', 'yellow'))

            if not test_QL_url(URL):
                URL = brute_force_QL_url(URL)

                if URL:
                    print(colored(f'[+] GraphQL endpoint found at {URL}', 'green'))
                    print(colored('[INFO] Introspection request ... ', 'blue'), end='')
                    
                    ql_introspection()
                    valid_url = True
                else:
                    print(colored(f'[-] No GraphQL endpoint found for {URL}', 'red'))
            else:
                print(colored(f'[+] {URL} is already an QL URL', 'green'))

        ####################################################################################
        #### HELP (show help)
        ####################################################################################
        elif user_input.lower() == 'h' or user_input.lower() == 'help':
            show_help()

        ####################################################################################
        #### INTROSPECTION (perform an introspection on the GraphQL endpoint)
        ####################################################################################
        elif user_input.lower() == "i" or user_input.lower() == "intro":
            ql_introspection()

        ####################################################################################
        #### EXIT (exit the program)
        ####################################################################################
        elif user_input == 'exit':
            break

      
        elif valid_url :
            ##############################################################################
            #### PROXY (set proxy)
            ##############################################################################
            if user_input.lower() == 'p' or user_input.lower() == 'proxy':
                print(colored('[INFO] Enter proxy host and port (default localhost:8080 - press enter) : ', 'blue'))
                host = input(colored('GQLHunter ~ PROXY ~ HOST> ', 'yellow'))
                port = input(colored('GQLHunter ~ PROXY ~ PORT> ', 'yellow'))
                
                if not host: host = 'localhost'
                if not port: port = '8080'

                config = uvicorn.Config("graphQLHunter:app", host=host, port=int(port))
                server = uvicorn.Server(config)
                server.run()
               

            ####################################################################################
            #### QUERY (perform query to the graphQL endpoint)
            ####################################################################################
            else:
                data = '' # reset data var
            
                user_input = user_input.replace('\\n', '').replace('\\', '') # sanitize the user input
                response   = requests.post(URL, json={'query': user_input}, headers=QL_HEADERS)

                try:
                    data = json.loads(response.text)

                    if 'errors' in data:
                        print(f'{colored("[-] Bad request :" + json.dumps(data["errors"], indent=4), "red")}')
                    else:
                        print(f'{colored(json.dumps(data, indent=4), "blue")}')

                except Exception as e:
                    print(colored('[-] Bad request !', 'red'))

        else:
            show_help()