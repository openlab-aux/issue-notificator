#! /usr/bin/env python3

import email.message as mail
import json
import subprocess as sub
import sys
import urllib.request as url
import urllib.error as urlerr

# Config
ORG = "openlab-aux"
REPO = "orgafoo"
NO_ISSUES = 10
ALT_ISSUE_URL = "https://issues.openlab-augsburg.de" # NULL if none
LIST_ADDRESS = "alle@lists.openlab-augsburg.de"
FROM_ADDRESS = "noreply@openlab-augsburg.de"
SUBJECT = "Die neuesten Openlab Issues für dich"

# Constants
GITHUB_ISSUE_URL = "https://api.github.com/repos/{org}/{repo}/issues"
GITHUB_REPO_ISSUE_URL = "https://github.com/{org}/{repo}/issues"


def grab_issues(organization, repo):
    """Grabs the issues from Github."""
    gurl = GITHUB_ISSUE_URL.format(org=organization, repo=repo)
    try:
        res = url.urlopen(gurl)
    except urlerr.HTTPError as e:
        if e.code == 404:
            raise NoRepoError("Repository or organization doesn’t exist.")
        else:
            raise
    return json.loads(res.read().decode())

class NoRepoError(Exception): pass
class GithubError(Exception): pass


def _mail_splitter(s, n):
    for start in range(0, len(s), n):
        yield s[start:start+n]

def display_issues(issues, issue_url, no_of_issues=10, line_length=69):
    """Takes the important parts and parses them for sending to list."""
    
    pre = """Hallo $Menschen,                                        
                                                                     
im Openlab sind in letzter Zeit einige Aufgaben angefallen, die gerne
erledigt werden möchten.                                             
                                                                     
Die letzten {n} Stück findet ihr hier, den Rest unter                
{url}                                                                

–––––––––––––––––––––––––––––––––––––––––––––––––––––––
    """.format(
        n = no_of_issues,
        url = issue_url
    )

    def get_issues(issues):
        for issue in issues[:no_of_issues]:
            yield "\n".join([
                issue['title'],
                " " + "•"*(len(issue['title'])-2) + " ",
                "\n".join(_mail_splitter(
                    issue['body'].replace("\r", " ").replace("\n", " "),
                    line_length
                )),
                issue['html_url'],
            ])
    issues_formatted = "\n\n\n".join(get_issues(issues))

    post = """–––––––––––––––––––––––––––––––––––––––––––––––––––––––

Happy Hacking!
"""

    return "\n\n".join([pre, issues_formatted, post])

def error(message):
    print("ERROR: " + message)
    
def send_mail_to_list(payload, subject, list_address, from_address):
    """Uses sendmail to get it out."""
    mes = mail.Message()
    mes["From"] = from_address
    mes["To"] = list_address
    mes["Subject"] = subject
    mes["Content-Type"] = "text/plain; charset=UTF-8"
    mes.set_payload(payload)

    try:
        with sub.Popen(["sendmail", "-t"], stdin=sub.PIPE, stderr=sub.PIPE) as send:
            _, errs = send.communicate(mes.as_string().encode())
            if send.poll() != 0:
                error("Sendmail failed with the following message:")
                sys.stderr.write(errs.decode())
                sys.exit()
            
    except FileNotFoundError:
        error("The sendmail program cannot be found.")
        sys.exit()


if __name__ == '__main__':
    issues = grab_issues(ORG, REPO)
    message = display_issues(
        issues,
        ALT_ISSUE_URL or GITHUB_REPO_ISSUE_URL.format(org=ORG, repo=REPO),
    )
    send_mail_to_list(message, SUBJECT, LIST_ADDRESS, FROM_ADDRESS)
