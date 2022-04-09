import json
import os
import requests
import shutil
import time
import threading

baseurl = 'https://registrationssb.ucr.edu/StudentRegistrationSsb/ssb'
basedir = 'api/v1'

def generate_output_folder():
  """
  Create output folder
  """
  if not os.path.isdir('api'):
    os.mkdir('api')
    os.mkdir(basedir)

def index_terms(terms):
  final_terms = []
  for term in terms:
    subject_params = {
      'term': term['code'],
      'offset': 1,
      'max': 500, # Again, hopefully this is enough
    }
    subjects = requests.get(f'{baseurl}/classSearch/get_subject', params = subject_params).json()
    # Let's not touch terms that have no data
    if (len(subjects) == 0):
      continue
    final_terms.append(term)
  with open(f'{basedir}/terms.json', 'w') as terms_file:
    terms_file.write(json.dumps(final_terms))

def thread_exec(session: requests.Session, terms):
  for term in terms:
    process_term(session, term['desc'], term['code'])

def process_term(session: requests.Session, desc: str, code: str):
  subject_params = {
    'term': code,
    'offset': 1,
    'max': 500, # Again, hopefully this is enough
  }

  # Should we force-update this quarter?
  view_only = 'View Only' in desc

  subjects = session.get(f'{baseurl}/classSearch/get_subject', params = subject_params).json()
  # Let's not touch terms that have no data
  if (len(subjects) == 0):
    return

  # Conditions for updating the repo with the current data
  term_output_dir = f'{basedir}/{code}'
  # 4/8/22 - design change - always update ALL terms, regardless of read only status
  # if not os.path.isdir(term_output_dir) or not view_only:
  if True:
    print(f'[{threading.current_thread().name}] Grabbing data for term {desc} ({len(subjects)} subjects). Force update? {"No" if view_only else "Yes"}')
    current_time = round(time.time() * 1000)
    temp_dir = f'{basedir}/{code}-{current_time}'
    os.mkdir(temp_dir)
    with open(f'{temp_dir}/subjects.json', 'w') as f:
      f.write(json.dumps(subjects))

    # Tentatively, this doesn't matter
    # It seems that banner ignores page parameters?
    page_max_size = 500

    course_params = {
      'txt_term': code,
      'txt_subject': 'None',
      'pageOffset': 0,
      'pageMaxSize': page_max_size
    }

    for subject in subjects:
      subject_code = subject['code']
      subject_desc = subject['description']
      subject_file = open(f'{temp_dir}/{subject_code}.json', 'w')
      
      course_params['txt_subject'] = subject_code
      course_params['pageOffset'] = 0
      lookup = course_lookup(session, course_params).json()

      lookup_data = {
        'code': subject_code,
        'description': subject_desc,
        'entries': lookup['totalCount'],
        'data': lookup['data']
      }

      subject_file.write(json.dumps(lookup_data))
      subject_file.close()
      print(f'[{threading.current_thread().name}] {code} {subject_code} success!')

      # while lookup['totalCount'] > 0:
      #   # Process the current lookup
      #   print(f'Found {lookup["totalCount"]} results for subject code {subject_code} in term {desc} on offset {course_params["pageOffset"]}')

      #   # Only process full pages
      #   # if lookup['totalCount'] < page_max_size:
      #   break

      #   # Increment the offset and continue
      #   course_params['pageOffset'] = course_params['pageOffset'] + page_max_size
      #   lookup = course_lookup(session, course_params).json()

    # Finalize updating
    if os.path.isdir(term_output_dir): # Remove old data if it exists
      shutil.rmtree(term_output_dir)
    os.rename(temp_dir, term_output_dir)
    print(f'[{threading.current_thread().name}] Successfully updated term {desc} to {term_output_dir}')

def course_lookup(session: requests.Session, lookup_params):
  session.post(f'{baseurl}/term/search?mode=search&term={lookup_params["txt_term"]}')
  result = session.get(f'{baseurl}/searchResults/searchResults', params = lookup_params)
  session.post(f'{baseurl}/classSearch/resetDataForm')
  return result

def main():
  generate_output_folder()
  session = requests.Session()

  with open(f'{basedir}/last_update.json', 'w') as last_update_file:
    data = {
      'last_update': round(time.time() * 1000)
    }
    last_update_file.write(json.dumps(data))

  term_params = { 
    "offset": 1,
    "max": 500, # This should be good enough for 100+ years
  }

  # NOTE: based on previous queries with banner, it seems
  # UCR only has class data as far back as Fall 2006
  terms = session.get(f'{baseurl}/classSearch/getTerms', params = term_params).json()
  index_terms(terms)

  # Recommend (4x +/- 1) threads to evenly distribute work/maximize efficiency
  # Even numbers will result in some threads finishing a lot faster than others
  max_threads = 5
  term_collection = []
  threads = []

  thread_index = 0
  for term in terms:
    code = term['code']
    desc = term['description']
    # Add new collection if possible
    if len(term_collection) <= thread_index:
      term_collection.append([])
    term_collection[thread_index].append({
      'code': code,
      'desc': desc
    })
    thread_index += 1
    if (thread_index >= max_threads):
      thread_index = 0

  for i in range(len(term_collection)):
    t = threading.Thread(name = f'th{i}', target = thread_exec, args = (requests.Session(), term_collection[i]))
    t.start()

  for thread in threads:
    thread.join()
  
if __name__ == '__main__':
  main()