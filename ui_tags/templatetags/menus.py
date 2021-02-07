from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import string
import config

register = template.Library()

# This sets the menu and submenu structure for items that need to indicate they are active
# in the top navigation area; And includes link information
# and also allows matching with current items for different display
#  structure: name, function, menu role, submenus
# Demo page and api doc do not have anything active in top nav section (MENU_PUBLIC)

# Nav that shows up for logged in users
MENU_USER = (
          (_("DASHBOARD"), 'ui_admin.dashboard', 'admin', ()),
          (_("MANAGE ID"), 'ui_manage.index', 'user', ()),
          (_("NEWS"), 'ui_home.learn', 'user', ()),
          (_("CREATE ID"), 'ui_create.index', 'user',
            ( (_("Simple"), 'ui_create.simple', 'user', ()),
              (_("Advanced"), "ui_create.advanced", 'user', ())
            )
          ),
          (_("ACCOUNT SETTINGS"), 'ui_account.edit', 'user', ()),
          (_("ABOUT US"), 'ui_about.us', 'user', ()),
          (_("CONTACT"), 'ui.contact', 'user', ()),
          (_("API"), 'ui_api.latest', 'user', ()),
        )

# Tertiary nav
MENU_DEMO = (
                (_("NEWS"), 'ui_home.learn', 'public', ()),
                (_("DEMO ID"), 'ui_demo.index', 'public',
                  ( (_("Simple"), 'ui_demo.simple', 'public', ()),
                    (_("Advanced"), "ui_demo.advanced", 'public', ())
                  )
                ),
                (_("ABOUT US"), 'ui_about.us', 'public', ()),
                (_("CONTACT"), 'ui.contact', 'public', ()),
                (_("API"), 'ui_api.latest', 'public', ()),
            )

# Dynamically created menu for subnav; Only displays for logged in users
@register.simple_tag
def menu_user(current_func, session):
  acc = ''
  for i, menu in enumerate(MENU_USER):
    if (menu[2] == 'admin' and session) or menu[2] != 'admin':
        acc += menu_user_item(menu, session,
      current_func == menu[1])
  return acc

@register.simple_tag
def menu_pub(current_func, session):
  acc = ''
  for i, menu in enumerate(MENU_DEMO):
      acc += menu_user_item(menu, session,
      current_func == menu[1])
  return acc

def menu_user_item(tup, session, is_current):
  u = reverse(tup[1]) or tup[1]
  link_class = "nav-link"
  drop_body = ""
  drop_attr = ""
  if is_current:
    class_name = "nav-item active"
  else:
    class_name = "nav-item"

  if len(tup[3]) > 0:
      class_name += " dropdown"
      drop_attr += 'id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"'
      link_class += " dropdown-toggle"
      drop_body += '<div class="dropdown-menu" aria-labelledby="navbarDropdown">'
      for menu in tup[3]:
          print(menu)
          li = reverse(menu[1])
          drop_body += '<a class="dropdown-item" href="%s">%s</a>' % (li,menu[0])

      drop_body += '</div>'

  acc = '<li class=\"' + class_name + '\"><a href=\"%s\" ' % u
  acc += 'class=\"' + link_class + '\" ' + drop_attr + '>%s</a>' % tup[0]
  acc += drop_body+'</li>'
  return acc

@register.simple_tag
def learn_breadcrumb(view_title, parent_dir_title=None, parent_dir_link=None):
  home = _("Home")
  learn = _("Learn")
  codeblock = '<div class="general__form"><ul class="breadcrumb">' + \
    '<li><a href="/">' + unicode(home) + '</a></li>' + \
    '<li><a href="/learn">' + unicode(learn) + '</a></li>'
  if parent_dir_title is not None:
    if parent_dir_link is None:
      parent_dir_link = ''
    parent_dir_title_tr = _(parent_dir_title)
    codeblock += '<li><a href="/learn/' + unicode(parent_dir_link) + '">' + \
      unicode(parent_dir_title_tr) + '</a></li>'
  codeblock += '<li class="active">' + unicode(view_title) + '</li></ul></div>'
  return codeblock

# Simply determines whether an element should be tagged as active; Only used for topmost nav
@register.simple_tag
def active(current_func, view_name):
  if string.split(current_func, '.')[1] == view_name:
    return 'active'
  elif string.split(string.split(current_func, '.')[0], '_')[1] == view_name:
    return 'active'
  return ''

# Simply determines whether an element should be tagged as active; Only used for topmost nav
@register.simple_tag
def getOptions(name):
  return config.get("DEFAULT.ezid_base_url")
