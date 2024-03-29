# from ckan.controllers import group
import datetime
# import json
import logging
import re
# from webhelpers.html import escape, HTML, literal, url_escape
# from ckan.common import _
import urlparse as urlparse

# import ckanext.hdx_theme.helpers.explorer_data as explorer
import ckanext.hdx_theme.version as version
import pylons.config as config

# import re
import ckan.authz as new_authz
import ckan.lib.base as base
import ckan.lib.datapreview as datapreview
import ckan.lib.helpers as h
import ckan.logic as logic
# from ckan.common import (
#     c, request
# )
# import sqlalchemy
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import (
    _, ungettext, c, request, json,
)
from ckan.plugins import toolkit

# import ckanext.hdx_theme.helpers.counting_actions as counting

log = logging.getLogger(__name__)

downloadable_formats = {
    'csv', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}


def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False


def is_not_zipped(res):
    url = res.get('url', 'zip').strip().lower()  # Default to zip so preview doesn't show if there is no url
    if re.search(r'zip$', url) or re.search(r'rar$', url):
        return False
    return True


NOT_HXL_FORMAT_LIST = ['zipped shapefile', 'zip', 'geojson', 'json', 'kml', 'kmz', 'rar', 'pdf', 'excel',
                       'zipped', 'docx', 'doc', '7z']


def _any(item, ext_list=NOT_HXL_FORMAT_LIST):
    return any(i in item for i in ext_list)


def is_not_hxl_format(res_format):
    if not res_format:
        return False
    return _any([res_format.lower()], NOT_HXL_FORMAT_LIST)


def get_facet_items_dict(facet, limit=1000, exclude_active=False):
    facets = h.get_facet_items_dict(
        facet, limit, exclude_active=exclude_active)
    filtered_no_items = c.search_facets.get(facet)['items'].__len__()
    # total_no_items = json.loads(
    #     count.CountController.list[facet](count.CountController()))['count']
    # if filtered_no_items <= 50 and filtered_no_items < total_no_items:
    #     no_items = filtered_no_items
    # else:
    #     no_items = total_no_items
    no_items = filtered_no_items

    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return (facets[:limit], no_items)
    else:
        return (facets, no_items)


def get_last_modifier_user(dataset_id=None, group_id=None):
    if group_id is not None:
        activity_objects = model.activity.group_activity_list(group_id, limit=1, offset=0)
    if dataset_id:
        activity_objects = model.activity.package_activity_list(dataset_id, limit=1, offset=0)
    if activity_objects:
        user = activity_objects[0].user_id
        t_stamp = activity_objects[0].timestamp
        user_obj = model.User.get(user)
        return {"user_obj": user_obj, "last_modified": t_stamp.isoformat()}

    # in case there is no update date it will be displayed the current date
    return {"user_obj": None, "last_modified": None}


def get_filtered_params_list(params):
    result = []
    for (key, value) in params.items():
        if key not in {'q', 'sort'}:
            result.append((key, value))
    return result


# def get_last_revision_package(package_id):
#     #     pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
#     #     pkg = pkg_list[0]
#     #     return pkg.latest_related_revision.id
#     activity_objects = model.activity.package_activity_list(
#         package_id, limit=1, offset=0)
#     if len(activity_objects) > 0:
#         activity = activity_objects[0]
#         return activity.revision_id
#     return None


# def get_last_revision_group(group_id):
#     #     grp_list  = model.Session.query(model.Group).filter(model.Group.id == group_id).all()
#     #     grp = grp_list[0]
#     #     last_rev = grp.all_related_revisions[0][0]
#     activity_objects = model.activity.group_activity_list(
#         group_id, limit=1, offset=0)
#     if len(activity_objects) > 0:
#         activity = activity_objects[0]
#         return activity.revision_id
#     return None


def get_last_revision_timestamp_group(group_id):
    activity_objects = model.activity.group_activity_list(
        group_id, limit=1, offset=0)
    if len(activity_objects) > 0:
        activity = activity_objects[0]
        return h.render_datetime(activity.timestamp)
    return None


def get_dataset_date_format(date):
    # Is this a range?
    drange = date.split('-')
    if len(drange) != 2:
        drange = [date]
    dates = []
    for d in drange:
        try:
            dt = datetime.datetime.strptime(d, '%m/%d/%Y')
            dates.append(dt.strftime('%b %-d, %Y'))
        except:
            return False
    return '-'.join(dates)


def get_group_followers(grp_id):
    result = logic.get_action('group_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': grp_id})
    return result


def hdx_dataset_follower_count(pkg_id):
    result = logic.get_action('dataset_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': pkg_id})
    return result


def get_group_members(grp_id):
    member_list = logic.get_action('member_list')(
        {'model': model, 'session': model.Session},
        {'id': grp_id, 'object_type': 'user'})
    result = len(member_list)
    return result


def hdx_get_user_info(user_id):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    try:
        user = tk.get_action('hdx_basic_user_info')(context, {'id': user_id})
    except logic.NotAuthorized:
        base.abort(403, _('Unauthorized to see organization member list'))
    return user


def markdown_extract_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.markdown_extract(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result


def render_markdown_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.render_markdown(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result


def methodology_bk_compat(meth, other, render=True):
    if not meth and not other:
        return (None, None)
    standard_meths = ["Census", "Sample Survey",
                      "Direct Observational Data/Anecdotal Data", "Registry", "Other"]
    if meth in standard_meths and meth != "Other":
        if render:
            return (meth, None)
        else:
            return (meth, None)
    elif other:
        if render:
            return ("Other", h.render_markdown(other))
        else:
            return ("Other", other)
    else:
        meth = meth.split('Other - ')
        if render:
            return ("Other", h.render_markdown(meth[0]))
        else:
            return ("Other", meth[0])


def render_date_from_concat_str(str, separator='-'):
    result = ''
    if str:
        strdate_list = str.split(separator)
        for index, strdate in enumerate(strdate_list):
            try:
                date = datetime.datetime.strptime(strdate.strip(), '%m/%d/%Y')
                render_strdate = date.strftime('%b %d, %Y')
                result += render_strdate
                if index < len(strdate_list) - 1:
                    result += ' - '
            except ValueError, e:
                log.warning(e)

    return result


def hdx_build_nav_icon_with_message(menu_item, title, **kw):
    htmlResult = h.build_nav_icon(menu_item, title, **kw)
    if 'message' not in kw or not kw['message']:
        return htmlResult
    else:
        newResult = str(htmlResult).replace('</a>',
                                            ' <span class="nav-short-message">{message}</span></a>'.format(
                                                message=kw['message']))
        return h.literal(newResult)


def hdx_build_nav_no_icon(menu_item, title, **kw):
    html_result = str(h.build_nav_icon(menu_item, title, **kw))
    print html_result
    start = html_result.find('<i ') - 1
    end = html_result.find('</i>') + 4
    if start > 0:
        new_result = html_result[0:start] + ' class="no-icon">' + html_result[end:]
    else:
        new_result = html_result
    print new_result
    return h.literal(new_result)


def hdx_linked_user(user, maxlength=0):
    response = h.linked_user(user, maxlength)
    changed_response = re.sub(r"<img[^>]+/>", "", response)
    return h.literal(changed_response)


def hdx_show_singular_plural(num, singular_word, plural_word, show_number=True):
    response = None
    if num == 1:
        response = singular_word
    else:
        response = plural_word

    if show_number:
        return str(num) + ' ' + response
    else:
        return response


def hdx_num_of_new_related_items():
    max_days = 30
    count = 0
    now = datetime.datetime.now()
    for related in c.pkg.related:
        if (related.created):
            difference = now - related.created
            days = difference.days
            if days < max_days:
                count += 1
    return count


def hdx_member_roles_list():
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    return tk.get_action('member_roles_list')(context, {})


def hdx_version():
    return version.hdx_version


def hdx_get_extras_element(data_dict, key='key', value_key='org_url', ret_key='value'):
    res = ''

    if value_key in data_dict:
        res = data_dict[value_key]
    else:
        extras = data_dict.get('extras', [])
        for ex in extras:
            if ex[key] == value_key:
                res = ex[ret_key]
    return res


def hdx_less_default():
    return """
@bodyBackgroundColor: @greenColor;
@navTabsActiveColor: @wfpBlueColor;
@orderByDropdownColor: @wfpBlueColor;
@defaultLinkColor: @wfpBlueColor;

@paginationActiveBackground: @wfpBlueColor;

@topLineItemNumberFontSize: 56px;
@topLineItemUnitFontSize: 28px;


@modalSubmitButtonBackgrColor: #FFFFFF;

@modalSubmitButtonColor: #888888;

@modalHeaderBackgroundColor: #EEEEEE;
@modalFooterBackgroundColor: #EEEEEE;"""


def load_json(obj, **kw):
    return json.loads(obj, **kw)


def escaped_dump_json(obj, **kw):
    # escapes </ to prevent script tag hacking.
    return json.dumps(obj, **kw).replace('</', '<\\/')


def hdx_group_followee_list():
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj,
               'for_view': True}

    list = logic.get_action('group_followee_list')(
        context, {'id': c.userobj.id})
    # filter out the orgs
    groups = [group for group in list if not group['is_organization']]

    return groups


def hdx_organizations_available_with_roles():
    organizations_available = h.organizations_available('read')
    if organizations_available and len(organizations_available) > 0:
        orgs_where_editor = []
        orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set(
            [org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id']
                                for org in h.organizations_available('admin')])

    for org in organizations_available:
        org['has_add_dataset_rights'] = True
        if am_sysadmin:
            org['role'] = 'sysadmin'
        elif org['id'] in orgs_where_admin:
            org['role'] = 'admin'
        elif org['id'] in orgs_where_editor:
            org['role'] = 'editor'
        else:
            org['role'] = 'member'
            org['has_add_dataset_rights'] = False

    organizations_available.sort(key=lambda y:
    y['display_name'].lower())
    return organizations_available


def hdx_remove_schema_and_domain_from_url(url):
    urlTuple = urlparse.urlparse(url)
    if url.endswith('/preview'):
        # this is the case when the file needs to be transformed
        # before it can be previewed

        modifiedTuple = (('', '') + urlTuple[2:6])
    else:
        # this is for txt files
        # we force https since otherwise the browser will
        # anyway block loading mixed active content
        modifiedTuple = (('',) + urlTuple[1:6])
    modifiedUrl = urlparse.urlunparse(modifiedTuple)
    return modifiedUrl


def hdx_get_ckan_config(config_name):
    return config.get(config_name)


def get_group_name_from_list(glist, gid):
    for group in glist:
        if group['id'] == gid:
            return group['title']
    return ""


def hdx_follow_link(obj_type, obj_id, extra_text, cls=None, confirm_text=None):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return h.snippet('search/snippets/follow_link.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         extra_text=extra_text,
                         confirm_text=confirm_text,
                         cls=cls)
    return ''


def follow_status(obj_type, obj_id):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return following
    return False


def one_active_item(items):
    for i in items:
        if i['active']:
            return True
    return False


def feature_count(features):
    count = 0
    for name in features:
        facet = h.get_facet_items_dict(name)
        for f in facet:
            count += f['count']
    return count


def hdx_follow_button(obj_type, obj_id, **kw):
    ''' This is a modified version of the ckan core follow_button() helper
    It returns a simple link for a bootstrap dropdown menu

    Return a follow button for the given object type and id.

    If the user is not logged in return an empty string instead.

    :param obj_type: the type of the object to be followed when the follow
        button is clicked, e.g. 'user' or 'dataset'
    :type obj_type: string
    :param obj_id: the id of the object to be followed when the follow button
        is clicked
    :type obj_id: string

    :returns: a follow button as an HTML snippet
    :rtype: string

    '''
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        follow_extra_text = _('This Data')
        if kw and 'follow_extra_text' in kw:
            follow_extra_text = kw.pop('follow_extra_text')
        return h.snippet('snippets/hdx_follow_button.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         follow_extra_text=follow_extra_text,
                         params=kw)
    return ''


def hdx_add_url_param(alternative_url=None, controller=None, action=None,
                      extras=None, new_params=None, unwanted_keys=[]):
    '''
    MODIFIED CKAN HELPER THAT ALLOWS REMOVING SOME PARAMS

    Adds extra parameters to existing ones

    controller action & extras (dict) are used to create the base url
    via url_for(controller=controller, action=action, **extras)
    controller & action default to the current ones

    This can be overriden providing an alternative_url, which will be used
    instead.
    '''

    params_nopage = [(k, v) for k, v in request.params.items()
                     if k != 'page' and k not in unwanted_keys]
    params = set(params_nopage)
    if new_params:
        params |= set(new_params.items())
    if alternative_url:
        return h._url_with_params(alternative_url, params)
    return h._create_url_with_params(params=params, controller=controller,
                                     action=action, extras=extras)


def hdx_resource_preview(resource, package):
    ## COPY OF THE DEFAULT HELPER BY THE SAME NAME BUT FORCES URLS OVER HTTPS
    '''
    Returns a rendered snippet for a embedded resource preview.

    Depending on the type, different previews are loadeSd.
    This could be an img tag where the image is loaded directly or an iframe
    that embeds a web page, recline or a pdf preview.
    '''

    if not resource['url']:
        return False

    format_lower = datapreview.res_format(resource)
    directly = False
    data_dict = {'resource': resource, 'package': package}

    if datapreview.get_preview_plugin(data_dict, return_first=True):
        url = tk.url_for(controller='package', action='resource_datapreview',
                         resource_id=resource['id'], id=package['id'], qualified=True)
    else:
        return False

    return h.snippet("dataviewer/snippets/data_preview.html",
                     embed=directly,
                     resource_url=url,
                     raw_resource_url=https_load(resource.get('url')))


def https_load(url):
    return re.sub(r'^http://', '//', url)


def count_public_datasets_for_group(datasets_list):
    a = len([i for i in datasets_list if i['private'] == False])
    return a


def check_all_str_fields_not_empty(dictionary, warning_template, skipped_keys=[], errors=None):
    for key, value in dictionary.iteritems():
        if key not in skipped_keys:
            value = value.strip() if value else value
            if not value:
                message = warning_template.format(key)
                log.warning(message)
                add_error('Empty field', message, errors)
                return False
    return True


def add_error(type, message, errors):
    if isinstance(errors, list):
        errors.append({'_type': type, 'message': message})


def hdx_popular(type_, number, min=1, title=None):
    ''' display a popular icon. '''
    from ckan.lib.helpers import snippet as snippet
    if type_ == 'views':
        title = ungettext('{number} view', '{number} views', number)
    elif type_ == 'recent views':
        title = ungettext('{number} recent view', '{number} recent views', number)
    elif type_ == 'downloads':
        title = ungettext('{number} download', '{number} downloads', number)
    elif not title:
        raise Exception('popular() did not recieve a valid type_ or title')
    return snippet('snippets/popular.html', title=title, number=number, min=min)


def hdx_license_list():
    license_touple_list = base.model.Package.get_license_options()
    license_dict_list = [{'value': _id, 'text': _title} for _title, _id in license_touple_list]
    return license_dict_list


def hdx_methodology_list():
    result = [{'value': '-1', 'text': '-- Please select --'}, {'value': 'Census', 'text': 'Census'},
              {'value': 'Sample Survey', 'text': 'Sample Survey'},
              {'value': 'Direct Observational Data/Anecdotal Data', 'text': 'Direct Observational Data/Anecdotal Data'},
              {'value': 'Registry', 'text': 'Registry'}, {'value': 'Other', 'text': 'Other'}]
    return result


def hdx_location_list():
    locations = logic.get_action('cached_group_list')({}, {})
    locations_dict_list = [{'value': loc.get('name'), 'text': loc.get('title')} for loc in locations]
    return locations_dict_list


def hdx_organisation_list():
    orgs = h.organizations_available('create_dataset')
    orgs_dict_list = [{'value': org.get('name'), 'text': org.get('title')} for org in orgs]
    return orgs_dict_list


def hdx_tag_list():
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        tags = logic.get_action('tag_list')(context, {})
        tags_dict_list = [{'value': tag, 'text': tag} for tag in tags]
        return tags_dict_list
    return []

def hdx_dataset_preview_values_list():
    import ckanext.hdx_package.helpers.custom_validator as vd
    result = [{'value': vd._DATASET_PREVIEW_FIRST_RESOURCE, 'text': 'Default (first resource with preview)'}]
    return result

def hdx_frequency_list(for_sysadmin=False, include_value=None):
    result = [
        {'value': '-999', 'text': '-- Please select --', 'onlySysadmin': False},
        {'value': '1', 'text': 'Every day', 'onlySysadmin': False},
        {'value': '7', 'text': 'Every week', 'onlySysadmin': False},
        {'value': '14', 'text': 'Every two weeks', 'onlySysadmin': False},
        {'value': '30', 'text': 'Every month', 'onlySysadmin': False},
        {'value': '90', 'text': 'Every three months', 'onlySysadmin': False},
        {'value': '180', 'text': 'Every six months', 'onlySysadmin': False},
        {'value': '365', 'text': 'Every year', 'onlySysadmin': False},
        {'value': '0', 'text': 'Live', 'onlySysadmin': False},
        {'value': '-2', 'text': 'As needed', 'onlySysadmin': False},
        {'value': '-1', 'text': 'Never', 'onlySysadmin': False},
    ]
    filtered_result = result
    if not for_sysadmin:
        filtered_result = [r for r in result if not r.get('onlySysadmin') or include_value == r.get('value')]

    return filtered_result


def hdx_get_frequency_by_value(value):
    freqs = hdx_frequency_list(for_sysadmin=True)
    for freq in freqs:
        if value == freq.get('value'):
            return freq.get('text')
    return ''


# def hdx_get_layer_info(id=None):
#     layer = explorer.explorer_data.get(id)
#     return layer


def hdx_get_carousel_list():
    return logic.get_action('hdx_carousel_settings_show')({}, {})


def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj
    }


def _get_action(action, data_dict):
    return toolkit.get_action(action)(_get_context(), data_dict)


def hdx_is_current_user_a_maintainer(maintainers, pkg):
    if c.user:
        current_user = _get_action('user_show', {'id': c.user})
        user_id = current_user.get('id')
        user_name = current_user.get('name')

        if maintainers and (user_id in maintainers or user_name in maintainers):
            return True

    return False


def hdx_is_sysadmin(user_id):
    import ckan.authz as authz
    user_obj = model.User.get(user_id)
    if not user_obj:
        return False
        # raise logic.NotFound
    user = user_obj.name
    return authz.is_sysadmin(user)

def hdx_organization_list_for_user(user_id):
    orgs = []
    if user_id:
        # context = {
        #     'model': model,
        #     'session': model.Session,
        # }
        # user = model.User.get(user_id)
        # if user:
        #     context['auth_user_obj'] = user
        #     context['user'] = user.name
        # return tk.get_action('organization_list_for_user')(context, {'id': user_id})
        return tk.get_action('hdx_organization_list_for_user')(_get_context(), {'id': user_id})
    return orgs

def hdx_dataset_is_hxl(tag_list):
    for tag in tag_list:
        if tag.get('name') == 'hxl' and tag.get('display_name') == 'hxl':
            return True
    return False
