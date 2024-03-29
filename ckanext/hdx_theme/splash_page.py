import re
from rdflib import Graph, Literal, BNode, RDF
from rdflib.namespace import Namespace

import ckan.lib.base as base
from ckan.lib.base import request
from ckan.lib.base import c, h
from ckan.lib.base import model
from ckan.lib.base import _
import ckan.logic as logic

from ckan.controllers.home import HomeController
from ckan.common import config


NotAuthorized = logic.NotAuthorized
check_access = logic.check_access
get_action = logic.get_action
abort = base.abort


def google_searchbox_data():
    SCHEMA = Namespace('http://schema.org/')
    ckan_url = config.get('ckan.site_url', 'https://data.humdata.org').replace('http://', 'https://')
    search_action_url = ckan_url + '/search?q={search_term_string}'

    website_node = BNode()
    g = Graph()
    g.bind('schema', SCHEMA)
    g.add((website_node, RDF.type, SCHEMA.WebSite))
    g.add((website_node, SCHEMA.url, Literal(ckan_url)))
    search_action = BNode()

    g.add((website_node, SCHEMA.potentialAction, search_action))
    g.add((search_action, RDF.type, SCHEMA.SearchAction))
    g.add((search_action, SCHEMA.target, Literal(search_action_url)))
    g.add((search_action, SCHEMA['query-input'], Literal('required name=search_term_string')))
    return g.serialize(format='json-ld', auto_compact=True)


structured_data = google_searchbox_data()


class SplashPageController(HomeController):
    group_type = 'group'

    def index(self):
        group_type = None
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        data_dict = {'all_fields': True, 'q': q}
        sort_by = c.sort_by_selected = request.params.get('sort')
        if sort_by:
            data_dict['sort'] = sort_by
        try:
            self._check_access('site_read', context)
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        # c.group_package_stuff = caching.cached_get_group_package_stuff()
        #
        # ##Removing groups without geojson for the map
        # c.group_map = []
        # for gp in c.group_package_stuff:
        #     '''
        #         Removed check for geojson data because in the new version this information
        #         does not come from the group_list action and for now we are not using the map.
        #         If we'll need this we should implement some caching functionality for this too.
        #     '''
        #     c.group_map.append(gp)

        if c.userobj is not None:
            site_title = config.get('ckan.site_title', 'CKAN')
            msg = None
            url = h.url_for(controller='user', action='edit')
            is_google_id = \
                c.userobj.name.startswith('https://www.google.com/accounts/o8/id')
            if not c.userobj.email and (is_google_id and not c.userobj.fullname):
                msg = _(u'Please <a href="{link}">update your profile</a>'
                        u' and add your email address and your full name. '
                        u'{site} uses your email address'
                        u' if you need to reset your password.'.format(
                    link=url, site=site_title))
            elif not c.userobj.email:
                msg = _('Please <a href="%s">update your profile</a>'
                        ' and add your email address. ') % url + \
                      _('%s uses your email address'
                        ' if you need to reset your password.') \
                      % site_title
            elif is_google_id and not c.userobj.fullname:
                msg = _('Please <a href="%s">update your profile</a>'
                        ' and add your full name.') % (url)
            if msg:
                h.flash_notice(msg, allow_html=True)

        # template_data = {
        #     'data': {
        #         'hdx.carousel.config': logic.get_action('hdx_carousel_settings_show')({}, {})
        #     }
        # }
        c.structured_data = structured_data
        return base.render('home/index.html', cache_force=True)

    def _check_access(self, action_name, *args, **kw):
        ''' select the correct group/org check_access '''
        return check_access(self._replace_group_org(action_name), *args, **kw)

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        if self.group_type == 'organization':
            string = re.sub('^group', 'organization', string)
        return string

    def _action(self, action_name):
        ''' select the correct group/org action '''
        return get_action(self._replace_group_org(action_name))

    def about(self, page):
        title = {'license': _('Data Licenses'),
                 'terms': _('Terms of Service')}
        html = {'license': 'home/snippets/hdx_licenses.html',
                'terms': 'home/snippets/hdx_terms_of_service.html'}

        titleItem = title.get(page)
        htmlItem = html.get(page)

        if titleItem is None:
            message = _("The requested about page doesn't exist")
            raise logic.ValidationError({'message': message}, error_summary=message)

        extraVars = {'title': titleItem, 'html': htmlItem, 'page': page}
        return base.render('home/about2.html', extra_vars=extraVars)

    def about_hrinfo(self):
        title = {'hr_info': _('Legacy HR Info')}
        html = {'hr_info': 'home/snippets/hdx_hr_info.html'}

        titleItem = title['hr_info']
        htmlItem = html['hr_info']

        if titleItem is None:
            message = _("The requested about page doesn't exist")
            raise logic.ValidationError({'message': message}, error_summary=message)

        extraVars = {'title': titleItem, 'html': htmlItem, 'page': 'hr_info'}
        return base.render('home/about2.html', extra_vars=extraVars)
