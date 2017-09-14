#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import json
import codecs
import requests
from bs4 import BeautifulSoup
sys.path.append("..")
import UnityAnalytics.upid as upid

PACKAGE_NAMES = 'package_names.txt'
APP_INFOS = 'apps.json'
DIFF_INFORS = 'diff.json'


def get_app_info(package_name):
    url = 'http://app.mi.com/details?id=' + package_name
    resp = requests.get(url=url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    intro = soup.select('div .intro-titles')[0].contents
    company = intro[0].contents[0]
    app_name = intro[1].contents[0]
    genre = intro[2].contents[1]

    details = soup.select('div .details')[0].contents[0].contents
    app_size = details[1].contents[0]
    current_version = details[3].contents[0]
    update_date = details[5].contents[0]
    app_id = details[9].contents[0]
    return {
        'package name': package_name,
        'app id': app_id,
        'app name': app_name,
        'company': company,
        'genre': genre,
        'current version': current_version,
        'update date': update_date,
        'app size': app_size
    }


def download_apk(package_name, app_id):
    url = 'http://app.mi.com/download/' + app_id
    apks_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'apks')
    if not os.path.exists(apks_dir):
        os.makedirs(apks_dir)
    apk_path = os.path.join(apks_dir, package_name + '.apk')
    try_count = 2
    while try_count > 0:
        try_count -= 1
        try:
            resp = requests.get(url=url, stream=True)
            file_content = open(apk_path, 'wb')
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    file_content.write(chunk)
            file_content.close()
            break
        except Exception, ex:
            print 'Got exception when downloading: ', ex
            file_content.close()
            os.remove(apk_path)
            if try_count == 0:
                apk_path = None
    return apk_path


def load_app_infos(app_infos_path):
    if not os.path.exists(app_infos_path):
        return {}
    file_content = open(app_infos_path)
    try:
        app_infos = json.load(file_content)
    except:
        app_infos = {}
    file_content.close()
    return app_infos


def save_app_infos(app_infos, app_infos_path):
    file_content = codecs.open(app_infos_path, 'w', encoding='utf-8')
    file_content.write(json.dumps(app_infos, ensure_ascii=False, indent=4, sort_keys=True))
    file_content.close()


def arr2dict(app_infos, key):
    dic = {}
    for info in app_infos:
        dic[info[key]] = info
    return dic


def get_upid(app_info):
    apk_path = download_apk(app_info['package name'], app_info['app id'])
    if not apk_path:
        print 'Download %s failed.' % app_info['package name']
    ua_info = upid.get_upid(apk_path)
    return ua_info[2] if ua_info[2] else ua_info[3]


def refresh(package_names_path, app_infos_path, diff_infors_path):
    file_content = open(package_names_path)
    old_app_infos = arr2dict(load_app_infos(app_infos_path), 'package name')
    diff_infos = []
    changed = False
    for line in file_content:
        package_name = line.strip()
        app_info = get_app_info(package_name)
        if old_app_infos.has_key(package_name):
            app_info['UPID'] = old_app_infos[package_name]['UPID']
            need_update = cmp(old_app_infos[package_name], app_info) != 0
            old_info = old_app_infos[package_name]
        else:
            need_update = True
            old_info = 'None'
        if need_update:
            app_info['UPID'] = get_upid(app_info)
            old_app_infos[package_name] = app_info
            diff_infos.append({'Old': old_info, 'New': app_info})
            changed = True
    file_content.close()
    if changed:
        save_app_infos(old_app_infos.values(), app_infos_path)
        save_app_infos(diff_infos, diff_infors_path)


def main():
    package_names_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), PACKAGE_NAMES)
    app_infos_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), APP_INFOS)
    diff_infors_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), DIFF_INFORS)
    refresh(package_names_path, app_infos_path, diff_infors_path)


if __name__ == '__main__':
    main()
