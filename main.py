import requests
import csv
import sys
 
bitbucket_url = sys.argv[1]
bb_api_url = bitbucket_url + '/rest/api/latest'
ag_api_url = bitbucket_url + '/rest/awesome-graphs-api/latest'
 
s = requests.Session()
s.auth = (sys.argv[2], sys.argv[3])
 
project_key = sys.argv[4]
 
 
def get_repos(project_key):
     
    repos = list()
 
    is_last_page = False
 
    while not is_last_page:
        request_url = bb_api_url + '/projects/' + project_key + '/repos'
        response = s.get(request_url, params={'start': len(repos), 'limit': 25}).json()
        for repo in response['values']:
            repos.append(repo['slug'])
        is_last_page =  response['isLastPage']
 
    return repos
 
 
def get_total_loc(repo_slug):
 
    url = ag_api_url + '/projects/' + project_key + \
          '/repos/' + repo_slug + '/commits/statistics'
    response = s.get(url).json()
    total_loc = response['linesOfCode']['added'] - response['linesOfCode']['deleted']
 
    return total_loc
 
 
with open('total_loc_per_repo.csv', mode='a', newline='') as report_file:
    report_writer = csv.writer(report_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    report_writer.writerow(['repo_slug', 'total_loc'])
 
    for repo_slug in get_repos(project_key):
        print('Processing repository', repo_slug)
        report_writer.writerow([repo_slug, get_total_loc(repo_slug)])
