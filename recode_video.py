# -*- coding: utf-8 -*-
from __future__ import print_function

import errno
import locale
import os
import re
import shutil
import subprocess
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT


def ensure_dir(path):
    """
    os.path.makedirs without EEXIST.
    Taken from pip.utils
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)


def main():
    usage = 'Usage: %prog [options]'
    parser = OptionParser(usage=usage)
    parser.add_option(
        '--audio-channel',
        choices=['both', 'left', 'right'],
        default='both',
        dest='audio_channel',
        help='Audio channel to use (both, left, right)',
    )
    parser.add_option(
        '--dir',
        default='.',
        dest='dir',
        help='Path to folder with DV/AVI files',
        type=str,
    )
    parser.add_option(
        '--save-temp',
        action='store_true',
        dest='save_temp_files',
        help='If chosen, temp files are not deleted (for debugging)',
    )
    options, args = parser.parse_args()
    working_dir = os.path.normpath(unicode(options.dir.decode(sys.getfilesystemencoding())))

    script_path = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = os.path.join(script_path, 'bin', 'ffmpeg.exe')
    x264_path = os.path.join(script_path, 'bin', 'x264.exe')

    temp_avs_path = os.path.join(working_dir, 'temp.avs')

    with open(temp_avs_path, 'w') as avs_file:
        avs_dll_path = os.path.join(script_path, 'bin', 'AviSynth_plugins', 'avss.dll')
        avs_file.write(r'LoadPlugin("{}")'.format(avs_dll_path) + '\n')
        my_deinterlace_path = os.path.join(script_path, 'bin', 'deinterlacers', 'my_deinterlace.avs')
        avs_file.write(r'import("{}")'.format(my_deinterlace_path) + '\n')
        avs_file.write(r'c = DSS2("temp")' + '\n')
        avs_file.write(r'return c.my_deinterlace()' + '\n')

    mov_folder = os.path.join(working_dir, 'mov')
    avi_folder = os.path.join(working_dir, 'avi')
    x264_folder = os.path.join(working_dir, 'x264')
    audio_folder = os.path.join(working_dir, 'audio')

    # Used temp paths
    temp_video_without_audio = os.path.join(x264_folder, 'video.mp4')
    temp_audio_uncompressed = os.path.join(audio_folder, 'audio.wav')

    for source_filename in os.listdir(working_dir):
        if source_filename.endswith('.avi') or source_filename.endswith('.dv'):
            print(source_filename)

            ensure_dir(mov_folder)
            ensure_dir(avi_folder)
            ensure_dir(x264_folder)
            ensure_dir(audio_folder)
            try:
                os.remove(temp_video_without_audio)
            except OSError:
                pass
            try:
                os.remove(temp_audio_uncompressed)
            except OSError:
                pass

            filename, extension = os.path.splitext(source_filename)
            input_video = os.path.join(working_dir, source_filename)
            output_video = os.path.join(working_dir, 'mov', filename + '.mov')
            temp_video_path = os.path.join(working_dir, 'temp')

            cmd = u'{ffmpeg} -i "{input_video}"'.format(
                ffmpeg=ffmpeg_path, input_video=input_video)
            p = Popen(cmd.encode(locale.getpreferredencoding()), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            output = p.stdout.read()
            sar_match = re.compile(r'SAR \d+:\d+').findall(output)
            if len(sar_match) == 1:
                sar = sar_match[0].replace(u'SAR ', u'').decode('utf8')
                sar = r'--sar ' + sar
            else:
                sar = r''

            input_audio_stream_id = ''
            input_acodec = ''
            if options.audio_channel in ('left', 'right'):
                audio_match = re.search(
                    r'Stream #(?P<astream>\d+:\d+): Audio: (?P<acodec>\w+)',
                    output)
                if audio_match:
                    audio_match_dict = audio_match.groupdict()
                    input_audio_stream_id = audio_match_dict['astream']
                    input_acodec = audio_match_dict['acodec']
                    if not input_acodec.startswith('pcm'):
                        print('Audio codec is not pcm_*. Only pcm codecs are '
                              'supported when manipulating audio channels.')
                        sys.exit(1)
                else:
                    print('Failed to extract audio codec information; '
                          'it is necessary when manipulating audio channels.')
                    sys.exit(1)

            shutil.move(input_video, temp_video_path)
            touch(input_video + '.lock')
            cmd = (
                u'{x264} --crf 15 --profile high --preset slow {sar} '
                u'-o "{temp_video_without_audio}" "{temp_avs_path}"'.format(
                    x264=x264_path,
                    sar=sar,
                    temp_video_without_audio=temp_video_without_audio,
                    temp_avs_path=temp_avs_path,
                )
            )
            subprocess.call(cmd.encode(locale.getpreferredencoding()))
            os.remove(input_video + '.lock')
            shutil.move(temp_video_path, input_video)

            if options.audio_channel in ('left', 'right'):
                if input_acodec and input_audio_stream_id:
                    if options.audio_channel == 'left':
                        achannel = 0
                    elif options.audio_channel == 'right':
                        achannel = 1
                    else:
                        raise RuntimeError('Failed to set achannel')
                    audio_options = '-map_channel {astream}.{achannel} -c:a {acodec}'.format(
                        astream=input_audio_stream_id.replace(':', '.'),
                        achannel=achannel,
                        acodec=input_acodec)
                else:
                    raise RuntimeError('input_acodec or input_audio_stream_id was not set')
            else:
                audio_options = '-c:a copy'

            cmd = u'{ffmpeg} -i "{input_video}" {audio_options} "{temp_audio_uncompressed}"'.format(
                ffmpeg=ffmpeg_path,
                input_video=input_video,
                audio_options=audio_options,
                temp_audio_uncompressed=temp_audio_uncompressed,
            )
            subprocess.call(cmd.encode(locale.getpreferredencoding()))

            cmd = (
                u'{ffmpeg} '
                u'-i "{temp_video_without_audio}" '
                u'-i "{temp_audio_uncompressed}" '
                u'-c:v copy -c:a copy "{output_video}"'.format(
                    ffmpeg=ffmpeg_path,
                    temp_video_without_audio=temp_video_without_audio,
                    temp_audio_uncompressed=temp_audio_uncompressed,
                    output_video=output_video,
                )
            )
            subprocess.call(cmd.encode(locale.getpreferredencoding()))

            shutil.move(input_video, avi_folder)
            if not options.save_temp_files:
                os.remove(temp_video_without_audio)
                os.remove(temp_audio_uncompressed)
                shutil.rmtree(x264_folder)
                shutil.rmtree(audio_folder)

    os.remove(temp_avs_path)


if __name__ == '__main__':
    main()
