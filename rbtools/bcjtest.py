from clients.getclient import get_client

#get the client
client = get_client('http://demo.reviewboard.org')

#get the lines that are different
(diff_lines, parent_diff_lines) = client.diff(None)

#create the diff file
file = open ('diff.diff', 'w' )

for line in diff_lines:
    file.write(line)
    
file.close()