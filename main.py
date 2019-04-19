import logging
import urllib
import os
import errno
import json

from datetime import datetime
from lib.api import API

# config
SITE_URL = 'https://pemilu2019.kpu.go.id/'
DOMAIN = 'hhcw'
SECTION = 'ppwp'
SAVE_LOG = True
SAVE_IMAGE = False
DUMP_API = False

candidates = {}
result = {}
messages = []

log = logging.getLogger(__name__)
api = API(SITE_URL, DUMP_API)

def get_metadata():
    global candidates

    version = api.get_json('version.json')
    log.critical('[SUMMARY] %s', version.get('version'))

    response = api.get_json(SECTION + '.json')
    candidates = response.items()

def show_summary():
    global candidates

    summary = api.get_json(DOMAIN, SECTION + '.json')
    chart = summary.get('chart')
    candidate_total = 0
    for (k, v) in chart.items():
        candidate_total += int(v)

    progress = summary.get('progress')
    proses = progress.get('proses')
    total = progress.get('total')
    percentage = round(100 * float(proses)/total, 2)
    log.critical('[SUMMARY] Progress %s of %s total pools (%.2f%%)', "{:,}".format(proses), "{:,}".format(total), percentage)

    for (k, v) in candidates:
        candidate_percentage = round(100 * float(chart.get(k))/candidate_total, 2)
        log.critical('[SUMMARY] %s', v.get('nama'))
        log.critical('[SUMMARY]     %s votes (%.2f%%)', "{:,}".format(chart.get(k)), candidate_percentage)

def show_result():
    global candidates
    global result

    candidate_total = 0
    for (k, v) in result.items():
        candidate_total += int(v)

    for (k, v) in candidates:
        candidate_percentage = round(100 * float(result.get(k))/candidate_total, 2)
        log.critical('[RESULT] %s', v.get('nama'))
        log.critical('[RESULT]     %s votes (%.2f%%)', "{:,}".format(result.get(k)), candidate_percentage)

    log.critical('[RESULT] Progress collected %s', "{:,}".format(candidate_total))

def validate_pools():
    global candidates

    regions = api.get_json('wilayah', '0.json')
    for (k0, v0) in regions.items():
        provinces = api.get_json('wilayah', k0 + '.json')
        for (k1, v1) in provinces.items():
            districts = api.get_json('wilayah', k0, k1 + '.json')
            for (k2, v2) in districts.items():
                subdistricts = api.get_json('wilayah', k0, k1, k2 + '.json')
                for (k3, v3) in subdistricts.items():
                    administratives = api.get_json('wilayah', k0, k1, k2, k3 + '.json')
                    for (k4, v4) in administratives.items():
                        check_one(k0, k1, k2, k3, k4, v0.get('nama'), v1.get('nama'), v2.get('nama'), v3.get('nama'), v4.get('nama'))

def check_one(k0, k1, k2, k3, k4, v0, v1, v2, v3, v4):
    global candidates
    global result

    pools = api.get_json(DOMAIN, SECTION, k0, k1, k2, k3, k4 + '.json')
    chart = pools.get('chart')
    images = pools.get('images')
    dpt_total = pools.get('pemilih_j')
    dpt_used = pools.get('pengguna_j')
    pool_valid = pools.get('suara_sah')
    pool_invalid = pools.get('suara_tidak_sah')
    pool_total = pools.get('suara_total')
    valid = True
    data_exist = False

    candidate_total = 0
    if chart is not None:
        data_exist = True
        for (k, v) in candidates:
            candidate_total += int(chart.get(k))
    else:
        data_exist = False

    if (int(pool_invalid or 0) + int(pool_valid or 0) != int(pool_total or 0)):
        save_log('[VALIDATION] VALIDATE ' + v0 + ' => ' + v1 + ' => ' + v2 + ' => ' + v3 + ' => ' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 1]: Total pool calculation mismatch!', k4)
        save_log('[VALIDATION] pool valid: ' + str(pool_valid), k4)
        save_log('[VALIDATION] pool invalid: ' + str(pool_invalid), k4)
        save_log('[VALIDATION] Total: ' + str(pool_valid + pool_invalid) + ' should be ' + str(pool_total), k4)
        save_data(k4, pools, images)
        valid = False;

    if (int(dpt_used or 0) != int(pool_total or 0)):
        save_log('[VALIDATION] VALIDATE ' + v0 + ' => ' + v1 + ' => ' + v2 + ' => ' + v3 + ' => ' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 2]: total DPT votes and total pool mismatch, it should be equal!', k4)
        save_log('[VALIDATION] DPT participation: ' + str(dpt_used), k4)
        save_log('[VALIDATION] pool total: ' + str(pool_total), k4)
        save_data(k4, pools, images)
        valid = False;

    if (int(pool_valid or 0) != int(candidate_total or 0)):
        save_log('[VALIDATION] VALIDATE ' + v0 + ' => ' + v1 + ' => ' + v2 + ' => ' + v3 + ' => ' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 3]: sum of candidates and total pool mismatch', k4)
        save_log('[VALIDATION] sum of candidates: ' + str(candidate_total), k4)
        save_log('[VALIDATION] pool total: ' + str(pool_valid), k4)
        save_data(k4, pools, images)
        valid = False;

    if data_exist:
        if valid:
            log.critical('[VALIDATION] VALIDATE %s => %s => %s => %s => %s', v0, v1, v2, v3, v4)
            log.critical('[VALIDATION] OK')
        else:
            log.critical('[VALIDATION] FAILED')

        for (k, v) in candidates:
            prev = result.get(k) if result.get(k) is not None else 0
            result[k] = prev + chart.get(k)
            if candidate_total != 0:
                candidate_percentage = round(100 * float(chart.get(k))/candidate_total, 2)
                log.critical('[VALIDATION] %s', v.get('nama'))
                log.critical('[VALIDATION]     %s votes (%.2f%%)', "{:,}".format(chart.get(k)), candidate_percentage)
    else:
        log.critical('[VALIDATION] VALIDATE %s => %s => %s => %s => %s', v0, v1, v2, v3, v4)
        log.critical('[VALIDATION] WAITING')

def save_log(message, pool):
    if SAVE_LOG:
        with open('log/' + datetime.now().strftime('result_' + pool + '_%Y%m%d.log'), "a") as output:
            output.write(message + '\n')

    log.critical(message)

def save_data(pool, result, images):
    if SAVE_LOG:
        with open('log/' + datetime.now().strftime('result_' + pool + '_%Y%m%d.log'), "a") as output:
            output.write(json.dumps(result) + '\n')

    if SAVE_IMAGE:
        for image in images:
            filename = 'log/' + datetime.now().strftime('result_' + pool + '_%Y%m%d/') + image
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise
            api.get_image(filename, pool[0:3], pool[3:6], pool, image)

def main():
    logging.basicConfig(
        format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s',
        # filename='log/'+datetime.now().strftime('output_%Y%m%d%H%M.log'),
        # filemode='a',
        level=logging.CRITICAL)
    # logging.getLogger().addHandler(logging.StreamHandler())
    logging.captureWarnings(True)
    get_metadata()
    validate_pools()
    # check_one('12920', '13905', '13906', '13907', '900070361', '1', '2', '3', '4', '5')
    show_result()
    show_summary()

if __name__ == '__main__':
    main()
