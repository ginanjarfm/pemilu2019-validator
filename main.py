import logging
import urllib
import os
import errno
import json
import argparse
import signal
import sys

from datetime import datetime
from lib.api import API

# config
DOMAIN = 'hhcw'
SECTION = 'ppwp'
SAVE_LOG = False
SAVE_IMAGE = False
DUMP_API = False

candidates = {}
result = {}
messages = []
state = []
version = None

log = logging.getLogger(__name__)
api = {}

def signal_handler(signal, frame):
    if (len(state) > 0):
        save_state(*state)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def get_metadata():
    global candidates
    global version

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
    global state

    last_state = read_state()
    state = last_state
    skip = len(last_state) == 5 or False
    if skip: log.critical('Skipping to ' + '-'.join(last_state))

    regions = api.get_json('wilayah', '0.json')
    for (k0, v0) in regions.items():
        if (skip and k0 == last_state[0]) or not skip:
            provinces = api.get_json('wilayah', k0 + '.json')
            for (k1, v1) in provinces.items():
                if (skip and k1 == last_state[1]) or not skip:
                    districts = api.get_json('wilayah', k0, k1 + '.json')
                    for (k2, v2) in districts.items():
                        if (skip and k2 == last_state[2]) or not skip:
                            subdistricts = api.get_json('wilayah', k0, k1, k2 + '.json')
                            for (k3, v3) in subdistricts.items():
                                if (skip and k3 == last_state[3]) or not skip:
                                    administratives = api.get_json('wilayah', k0, k1, k2, k3 + '.json')
                                    for (k4, v4) in administratives.items():
                                        if (skip and k4 == last_state[4]) or not skip:
                                            check_one(k0, k1, k2, k3, k4, v0.get('nama'), v1.get('nama'), v2.get('nama'), v3.get('nama'), v4.get('nama'))
                                            state = [k0, k1, k2, k3, k4]
                                            if skip:
                                                skip = False
                                                clear_state()

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

    candidate_message = ''
    margin = []
    candidate_total = 0
    if chart is not None:
        data_exist = True
        for (k, v) in candidates:
            candidate_message += 'suara [' + v.get('nomor_urut') + ']: ' + str(chart.get(k)) + '; '
            margin.append(str(chart.get(k)))
            candidate_total += int(chart.get(k))
    else:
        data_exist = False

    if (int(pool_invalid or 0) + int(pool_valid or 0) != int(pool_total or 0)):
        save_log('[VALIDATION] VALIDATE [' + k0 + ']' + v0 + ' => [' + k1 + ']' + v1 + ' => [' + k2 + ']' + v2 + ' => [' + k3 + ']' + v3 + ' => [' + k4 + ']' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 1]: Total pool calculation mismatch!', k4)
        save_log('[VALIDATION] pool valid: ' + str(pool_valid), k4)
        save_log('[VALIDATION] pool invalid: ' + str(pool_invalid), k4)
        save_log('[VALIDATION] Total: ' + str(pool_valid + pool_invalid) + ' should be ' + str(pool_total), k4)
        save_data(k4, pools, images)
        diff = abs((int(pool_invalid or 0) + int(pool_valid or 0)) - int(pool_total or 0))
        save_log('[VALIDATION] [DIFF 1]: ' + str(diff), k4)
        save_csv(
            str(k0) + '_' + str(v0).replace(' ', '_'),
            str(v0),
            str(v1),
            str(v2),
            str(v3),
            str(v4),
            '[F1] Jumlah seluruh suara sah dan suara tidak sah tidak sesuai',
            'suara sah: ' + str(pool_valid) + '; suara tidak sah: ' + str(pool_invalid) + '; total tertulis: ' + str(pool_total) + '; total terhitung: ' + str(pool_valid + pool_invalid))
        valid = False;

    if (int(dpt_used or 0) != int(pool_total or 0)):
        save_log('[VALIDATION] VALIDATE [' + k0 + ']' + v0 + ' => [' + k1 + ']' + v1 + ' => [' + k2 + ']' + v2 + ' => [' + k3 + ']' + v3 + ' => [' + k4 + ']' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 2]: total DPT votes and total pool mismatch!', k4)
        save_log('[VALIDATION] DPT participation: ' + str(dpt_used), k4)
        save_log('[VALIDATION] pool total: ' + str(pool_total), k4)
        save_data(k4, pools, images)
        diff = abs(int(dpt_used or 0) - int(pool_total or 0))
        save_log('[VALIDATION] [DIFF 2]: ' + str(diff), k4)
        save_csv(
            str(k0) + '_' + str(v0).replace(' ', '_'),
            str(v0),
            str(v1),
            str(v2),
            str(v3),
            str(v4),
            '[F2] jumlah pengguna hak pilih tidak sesuai dengan jumlah seluruh suara sah dan tidak sah',
            'pengguna hak pilih: ' + str(dpt_used) + '; jumlah suara sah dan tidak sah terhitung: ' + str(pool_total))
        valid = False;

    if (int(pool_valid or 0) != int(candidate_total or 0)):
        save_log('[VALIDATION] VALIDATE [' + k0 + ']' + v0 + ' => [' + k1 + ']' + v1 + ' => [' + k2 + ']' + v2 + ' => [' + k3 + ']' + v3 + ' => [' + k4 + ']' + v4 + '', k4)
        save_log('[VALIDATION] [FAILED 3]: sum of candidates and valid pool mismatch!', k4)
        save_log('[VALIDATION] sum of candidates: ' + str(candidate_total), k4)
        save_log('[VALIDATION] pool valid: ' + str(pool_valid), k4)
        save_data(k4, pools, images)
        diff = abs(int(pool_valid or 0) - int(candidate_total or 0))
        save_log('[VALIDATION] [DIFF 3]: ' + str(diff), k4)
        save_csv(
            str(k0) + '_' + str(v0).replace(' ', '_'),
            str(v0),
            str(v1),
            str(v2),
            str(v3),
            str(v4),
            '[F3] Total perolehan suara 01 & 02 tidak sesuai dengan jumlah seluruh suara sah',
            candidate_message + 'jumlah seluruh suara sah: ' + str(pool_valid) + '; terhitung: ' + str(candidate_total), *margin)
        valid = False;

    if data_exist:
        if valid:
            log.critical('[VALIDATION] VALIDATE [%s]%s => [%s]%s => [%s]%s => [%s]%s => [%s]%s', k0, v0, k1, v1, k2, v2, k3, v3, k4, v4)
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
        log.critical('[VALIDATION] VALIDATE [%s]%s => [%s]%s => [%s]%s => [%s]%s => [%s]%s', k0, v0, k1, v1, k2, v2, k3, v3, k4, v4)
        log.critical('[VALIDATION] WAITING')

def save_csv(region, *args):
    if not os.path.isfile('log/' + datetime.now().strftime('%Y%m%d_' + region + '.csv')):
        with open('log/' + datetime.now().strftime('%Y%m%d_' + region + '.csv'), "a") as output:
            output.write(version.get('version') + '\n')
            output.write(','.join(['Provinsi', 'Kab/Kota', 'Kecamatan', 'Kelurahan', 'TPS', 'Jenis Kesalahan', 'Keterangan']) + '\n')
    with open('log/' + datetime.now().strftime('%Y%m%d_' + region + '.csv'), "a") as output:
        output.write(','.join(args) + '\n')

def save_log(message, pool):
    if SAVE_LOG:
        with open('log/' + datetime.now().strftime('%Y%m%d_' + pool + '.log'), "a") as output:
            output.write(message + '\n')

    log.critical(message)

def save_data(pool, result, images):
    if SAVE_LOG:
        with open('log/' + datetime.now().strftime('%Y%m%d_' + pool + '.log'), "a") as output:
            output.write(json.dumps(result) + '\n')

    if SAVE_IMAGE:
        for image in images:
            filename = 'log/' + datetime.now().strftime('%Y%m%d_' + pool + '/') + image
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise
            api.get_image(filename, pool[0:3], pool[3:6], pool, image)

def save_state(*args):
    log.critical('[STATE] Saving last state')
    with open('.state', "w") as f:
        f.writelines(["%s\n" % item  for item in args])

def read_state():
    log.critical('[STATE] Read last state')
    with open('.state') as f:
        content = f.readlines()
    return [x.strip() for x in content]

def clear_state():
    log.critical('[STATE] Clear last state')
    with open('.state', "w") as f:
        f.write('')

def main():
    global api
    global SAVE_LOG, SAVE_IMAGE, DUMP_API

    parser = argparse.ArgumentParser(description='Arguments')
    parser.add_argument('--site_url', help='run with site_url', required=True)
    parser.add_argument('--save_log', help='save failure validation')
    parser.add_argument('--save_image', help='save failure validation image')
    parser.add_argument('--dump_api', help='dump data')
    parser.add_argument('--restart', help='restart state from the beginning', action='store_true')
    args = parser.parse_args()

    SAVE_LOG = args.save_log or SAVE_LOG
    SAVE_IMAGE = args.save_image or SAVE_IMAGE
    DUMP_API = args.dump_api or DUMP_API

    api = API(args.site_url, DUMP_API)

    logging.basicConfig(
        format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s',
        # filename='log/'+datetime.now().strftime('output_%Y%m%d%H%M.log'),
        # filemode='a',
        level=logging.CRITICAL)
    # logging.getLogger().addHandler(logging.StreamHandler())
    logging.captureWarnings(True)

    if args.restart:
        clear_state()

    get_metadata()
    validate_pools()
    # check_one('6728', '11916', '11965', '11966', '900052080', '6728', '11916', '11965', '11966', '900052080')
    show_result()
    show_summary()

if __name__ == '__main__':
    main()
