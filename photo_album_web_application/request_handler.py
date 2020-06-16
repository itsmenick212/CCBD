import boto3
import json
import requests



def request_handler(event, context):
    print(event)
    # print(str(json.dumps(event)))

    key1 = None
    key2 = None
    
    print('searching now')
   
    if 'Key1' in event["queryStringParameters"]:
        key1 = event["queryStringParameters"]["Key1"]
        print("The key got here "+key1)
    if 'Key2' in event["queryStringParameters"]:
        key2 =  event["queryStringParameters"]["Key2"]
        print("Got the second key as "+key2)
    
    # lex = boto3.client('lex-runtime')
    
    # response = lex.post_text(
    # botName='searchImage',
    # botAlias="searchImageBot",
    # userId="nick-gupta",
    # inputText="show me dog and cat"
    # )
    
    # #print("The userId sending "+str(userId))
    # print("The response from lex is "+str(response))
    # print("The request is "+str(event))
    
    slot1,slot2 = get_slots_from_lex(key1)
    
  
    output = search_es(key1,key2)
    responseArray = []
    if output is not None:
        for i in output:
            print("i is "+str(i))
            j = json.loads(output[i])
            print("j is "+str(j))
            json_object = {}
            json_object['imageUrl'] = "https://s3.amazonaws.com/" + j["bucket"] + "/" + j["key"]
            responseArray.append(json_object)
                
        print (responseArray)
    
    
    resp = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type":"application/json"},
        "body": json.dumps(responseArray)
    }
    
    
    print("Sending response")
    return resp

def get_slots_from_lex(key1):
    lex = boto3.client('lex-runtime')
    
    response = lex.post_text(
    botName='searchImage',
    botAlias="searchImageBot",
    userId="nick-gupta",
    inputText="show me dog and cat"
    )
    
    #print("The userId sending "+str(userId))
    print("The response from lex is "+str(response))
    slot1 = response['slots']['queryone']
    slot2 = response['slots']['querytwo']
    
    return slot1,slot2

def search_es(key1,key2):
    print ("Entered ....")
    #print (key1 + " ... " + key2)
    data = {}
    data1 = {}
    data2 = {}
    if key1 is None and key2 is None:
        print("Both keys are none")
        
    
    
    if key2 == None:
        print ("Entered")
        API_ENDPOINT2 = "https://vpc-photos-syjqysac4x5asu6rpjuinxvsjq.us-east-1.es.amazonaws.com/photos/_search?q="+key1
        r2 = requests.get(url = API_ENDPOINT2)
        _json = r2.content.decode('utf8').replace("'", '"')
        data = json.loads(_json)
        
    elif key1 == None:
         API_ENDPOINT2 = "https://vpc-photos-syjqysac4x5asu6rpjuinxvsjq.us-east-1.es.amazonaws.com/photos/_search?q="+key2
         r2 = requests.get(url = API_ENDPOINT2)
         _json = r2.content.decode('utf8').replace("'", '"')
         data = json.loads(_json)
       
    else:
        API_ENDPOINT2_1 = "https://vpc-photos-syjqysac4x5asu6rpjuinxvsjq.us-east-1.es.amazonaws.com/photos/_search?q="+key1
        r1 = requests.get(url = API_ENDPOINT2_1)
        _json1 = r1.content.decode('utf8').replace("'", '"')
        data1 = json.loads(_json1)
        print(data1)
        
        API_ENDPOINT2_2 = "https://vpc-photos-syjqysac4x5asu6rpjuinxvsjq.us-east-1.es.amazonaws.com/photos/_search?q="+key2
        r2 = requests.get(url = API_ENDPOINT2_2)
        _json2 = r2.content.decode('utf8').replace("'", '"')
        data2 = json.loads(_json2)
        print(data2)
    
   
    output = {}
    
    ##only one key is query
    if 'hits' in data:
        for val in data['hits']['hits']:
            mdata = {}
            mdata['key'] = val['_source']['objectKey']
            mdata['bucket'] = val['_source']['bucket']
            json_data = json.dumps(mdata)
            if mdata['key'] not in output:  #put it
                output[mdata['key']] = json_data
            #otherwise skip it
        
    elif 'hits' in data1 and 'hits' in data2:
        mdata = {}
        
        for val in data1['hits']['hits']:
            mdata['key'] = val['_source']['objectKey']
            mdata['bucket'] = val['_source']['bucket']
            json_data = json.dumps(mdata)
            if mdata['key'] not in output:
                output[mdata['key']] = json_data
            #otherwise skip it
           
        for val in data2['hits']['hits']:
            mdata['key'] = val['_source']['objectKey']
            mdata['bucket'] = val['_source']['bucket']
            json_data = json.dumps(mdata)
            if mdata['key'] not in output:
                output[mdata['key']] = json_data
            #otherwise skip it

    print(output)
    return output
