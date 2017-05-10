''' 
This lambda function is triggered by a commit to a particular branch. 
It then checks for changes to the branch since the last commmit, and pushes those changes to an S3 bucket.
'''

import boto3

bucket_name = "<bucket-name>"
repo_name = "<repo-name>"
branch_name = "<branch-name>"
path_name = "<folder-in-branch>"  # root directory in git repo of bucket contents -- avoids copying root/.git stuff.

s3 = boto3.resource('s3')  # http://boto3.readthedocs.io/en/latest/reference/services/s3.html
bucket = s3.Bucket(bucket_name)
client = boto3.client('codecommit')  # boto3.readthedocs.io/en/latest/reference/services/codecommit.html

content_types = {
    'html':'text/html', 
    'htm':'text/html',
    'doc':'application/msword',
    'pdf':'application/pdf',
    'zip':'application/zip',
    'mpeg':'audio/mpeg',
    'css':'text/css',
    'bmp':'image/bmp',
    'gif':'image/gif',
    'jpeg':'image/jpeg',
    'png':'image/png',
    'tiff':'image/tiff',
    'rtf':'text/rtf',
    'txt':'text/plain',
    'md':'text/plain'}
default_type = 'binary/octet-stream'

def get_parent_commit_id():
    tags = bucket.Tagging()
    print(tags)
    return tags.tag_set[0]['Value']

def put_new_parent_id(commit_id):
    tags = bucket.Tagging()
    tags.put( Tagging={'TagSet':[{'Key':'last_id', 'Value':commit_id}]} )

def get_diffs(client):
    ''' Gets the contents of the current commit and previously recorded '''

    # find the latest commit ID
    release_branch = client.get_branch(repositoryName=repo_name, branchName=branch_name) 
    latest_commit_id = release_branch['branch']['commitId']
    
    latest_commit = client.get_commit(repositoryName=repo_name, commitId=latest_commit_id)['commit']
    parent_commit_id = get_parent_commit_id()
    
    put_new_parent_id(latest_commit_id)
    
    # get the files changed in that commit..
    diffs_current = client.get_differences(repositoryName=repo_name, afterCommitSpecifier=latest_commit_id, afterPath=path_name)['differences']
    diffs_parent  = client.get_differences(repositoryName=repo_name, afterCommitSpecifier=parent_commit_id, afterPath=path_name)['differences']
    return diffs_current, diffs_parent

def guess_content_type(name, content):
    ''' Figure out the content type of the blob '''
    
    extn = name.split('.')[-1]
    if extn in content_types:
        return content_types[extn]
    
    elif '<html>' in content:
        # by checking this, can pick up html files that lack an extension
        return 'text/html'
     
    else:
        return default_type

def lambda_handler(event, context):
    
    ''' figure out what has changed since last commit, push those changes to S3 bucket '''
    diffs_current, diffs_parent = get_diffs(client)
    
    # make dictionary of both diffs
    current_dict = dict()
    for d in diffs_current:
        blob = d['afterBlob']
        current_dict[blob['path']] = blob['blobId']
    
    parent_dict = dict()
    for d in diffs_parent:
        blob = d['afterBlob']
        parent_dict[blob['path']] = blob['blobId']
    
    # check for removed files, delete them
    to_delete = []  # {Key: object key}
    for b in parent_dict:
        if b not in current_dict:
            to_delete.append({'Key':b})
    
    if len(to_delete) > 0:
        bucket.delete_objects(Delete={'Objects':to_delete})
    
    for b in diffs_current:
        # if previously filtered to path, then '<path>/' is omitted! (so S3 directory starts from there)
        blob_name = b['afterBlob']['path']  
        blob_id = b['afterBlob']['blobId']
        
        if (blob_name not in parent_dict) or (parent_dict[blob_name] != blob_id):
            print( "{0}: will be updated".format(blob_name) )
            
            # check content type
            blob_content = client.get_blob(repositoryName=repo_name, blobId=blob_id)['content']
            content_type = guess_content_type(blob_name, blob_content)

            # copy this file to S3
            bucket.put_object(Key=blob_name, Body=blob_content, ContentType=content_type)
            
    return "completed codecommit to S3 function"