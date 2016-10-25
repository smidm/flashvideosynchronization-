import numpy as np
import os
import cv2
from synchronization import MultipleVideoSynchronization
import parameters
import logging
import pickle
import datetime
logging.basicConfig(level=logging.INFO)


def compute_luminance_median(img):
    return np.median(cv2.cvtColor(img, cv2.COLOR_RGB2Lab)[:, :, 0], axis=1)


def extract_features(image_sequence, feature_func, camera, frame_start=0, frame_end=-1, dtype=np.float16):
    # features = np.zeros((image_sequence.get_image(0, camera).shape[0], frame_end - frame_start), dtype=dtype)
    features = []

    if frame_end == -1:
        frame_end = int(image_sequence.frame_count[camera])
    image_sequence.seek(frame_start)
    for i, frame in enumerate(xrange(frame_start, frame_end)):
        try:
            # img = image_sequence.get_image(frame, camera)
            img = image_sequence.get_next_image(camera)
        except IOError:
            break
        features.append(feature_func(img))
        # features[:, i] =
        if (i % 10) == 0:
            # print("cam %d: %d / %d" % (camera, i, frame_end - frame_start))
            logging.info("cam %d: %d / %d" % (camera, i, frame_end - frame_start))
    return np.array(features, dtype=dtype).T

if __name__ == '__main__':
    sequence_length_sec = 600
    ocred_timings = 'video/usa_rus/frame_timings.pkl'
    root = '../data/ihwc2015/'
        # '../data/ihwc2015/video/usa_rus/'

    out_dir = 'out/'
    features_file = os.path.join(out_dir, 'flashes2d_luminance_median_noseek.pkl')
    out_feature_images = os.path.join(out_dir, '%d.png')

    # /home/matej/prace/sport_tracking/git/experiments/2016-08-22_subframe_synchronization
    p = parameters.Parameters('parameters.yaml')
    # p.c['data_root'] = root
    del p.c['background_subtraction']['masks']
    # bgs = p.get_foreground_sequence()
    images = p.get_image_sequence()
    sync = MultipleVideoSynchronization()
    sync.load(os.path.join(p.c['data_root'], ocred_timings))
    match_start = np.datetime64('1900-01-01T' + p.c['match_start'])

    if os.path.exists(features_file):
        with open(features_file, 'rb') as fr:
            features = pickle.load(fr)
            features_start = pickle.load(fr)
    else:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        features = {}
        features_start = {}
        print datetime.datetime.now()

        for cam in p.c['cameras']:
            start = np.searchsorted(sync.get_timings()[cam], match_start)
            end = np.searchsorted(sync.get_timings()[cam], match_start + np.timedelta64(sequence_length_sec, 's'))
            features_start[cam] = start
            features[cam] = extract_features(images, compute_luminance_median, cam, start, end, dtype=np.uint8)
            print datetime.datetime.now()

            # img = cv2.normalize(features[cam].astype(float),
            #                     np.zeros_like(features[cam], dtype=float),
            #                     0, 255, cv2.NORM_MINMAX, dtype=8)
            # cv2.imwrite(out_feature_images % cam, img)

        with open(features_file, 'wb') as fw:
            pickle.dump(features, fw)
            pickle.dump(features_start, fw)
