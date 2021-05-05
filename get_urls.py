import urllib.request
from bs4 import BeautifulSoup

'''
textToSearch = 'hello world'
query = urllib.parse.quote(textToSearch)
url = "https://www.youtube.com/results?search_query=" + query
response = urllib.request.urlopen(url)
print(list(response))
html = response.read()
soup = BeautifulSoup(html, 'html.parser')

for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
	print('ye')
	print('https://www.youtube.com' + vid['href'])
'''

import urllib.request
import re

search_term = str(input('what term do you want to search? \n'))
html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_term)
video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
print(video_ids)