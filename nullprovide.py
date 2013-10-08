''' nullprovide -- Andrew's fork
Copyright (c) 2012, timdoug (me@timdoug.com)
Copyright (c) 2013, Andrew Francis (andrew@sullust.net)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the timdoug, Bump Technologies, Inc., nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import urllib2
import datetime
from bs4 import BeautifulSoup

class NullProvide(object):

    def __init__(self, account_key, string_dates=False):
        text = urllib2.urlopen('http://www.zerocater.com/menu/%s/' % account_key).read()
        self.soup = BeautifulSoup(text, "html5lib")

        self.meals = []
        for menu in self.soup.findAll('div', 'menu'):
            def parse_date():
                time_raw = menu.find('div', 'header-time').text.split()
                year, month, day = map(int, menu.attrs['data-date'].split('-'))
                hour, minute = map(int, time_raw[-2].split(':'))
                hour += 12 if time_raw[-1] == 'p.m.' and hour != 12 else 0
                out = datetime.datetime(year, month, day, hour, minute)
                return str(out) if string_dates else out

            def rating_from_class(classes):
                for x in xrange(10,51,10):
                    if ('rating-%s' % (x,)) in classes:
                        return x / 10
                return None

            def safe_text(elem):
                text = elem.text if elem else ''
                stripped = text.strip() if text else ''
                return stripped if stripped else None

            def parse_user_feedback(b):
                if not b:
                    return []

                feedback = []
                for comment in b.findAll('div', 'old-comment'):
                    if comment.findAll('div', 'admin-name'):
                        staff_comment = safe_text(comment.find('div', 'old-comment-body'))
                        if feedback:
                            feedback[-1]['staff_response'] = safe_text(comment.find('div', 'old-comment-body'))
                    else:
                        # Skip everything except the first, overall rating from someone
                        user = comment.find('div', 'commenter-name')
                        if user:
                            feedback.append({'user': user.text.strip(),
                                         'rating': rating_from_class(comment.find('span', 'rating-given')['class']),
                                         'comment': safe_text(comment.find('div', 'old-comment-body')),
                                         'staff_response': None})

                return feedback

            def parse_items(ul):
                if not ul:
                    return []

                items = []
                for li in ul.findAll('li', 'item'):
                    name = safe_text(li.find('span', 'item-name'))
                    details = li.findAll('div', 'item-description') + li.findAll('div', 'item-instructions')
                    if name:
                        items.append({'name': name})
                        if details:
                            items[-1]['details'] = "\n".join(safe_text(d) for d in details)

                return items

            self.meals.append({'name': menu.find('div', 'order-name').text.strip(),
                               'restaurant': menu.find('div', 'vendor').text.strip(),
                               'items': parse_items(menu.find('ul', 'item-list')),
                               'feedback': parse_user_feedback(menu.find('div', 'old-comments-container')),
                               'date': parse_date()})


if __name__ == '__main__':
    import sys
    import json
    if len(sys.argv) != 2:
        print 'usage: %s account_key' % sys.argv[0]
        sys.exit(1)
    print json.dumps(NullProvide(sys.argv[1], string_dates=True).meals, indent=4, sort_keys=True)

