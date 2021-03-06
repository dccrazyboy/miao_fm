#!/usr/bin/env python
#coding:utf8
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../')
import datetime
import random
import json
import traceback

import mutagen
import mid3iconv
import mongoengine.errors
from mongoengine import *

from user.model import UserSet


class Music(Document):
    '''
    store music info
    all item and functions start with *music_* will be auto serialized
    '''
    # music meta
    music_name = StringField(max_length=200, default='')
    music_artist = StringField(max_length=50, default='')
    music_album = StringField(max_length=100, default='')
    music_tag = DictField()
    music_img = StringField(max_length=200, default='')
    music_played = IntField(default=0)
    music_voted = DictField()

    # file info
    music_file = FileField('miao_fm_cdn')
    music_img_file = FileField('miao_fm_cdn')

    # upload info
    music_upload_user = ReferenceField('user.model.User', reverse_delete_rule=NULLIFY)
    music_upload_date = DateTimeField()

    @property
    def music_id(self):
        return self.pk

    @property
    def music_url(self):
        try:
            return '/music_file/%s/' % (self.music_file._id)
        except:
            return ''

    @property
    def img_url(self):
        try:
            return '/music_img/%s/' % (self.music_img_file._id)
        except:
            return self.music_img

    meta = {
        'ordering': ['-music_upload_date']
    }

    def __str__(self):
        return ('music_name = %s' % (self.music_name)).encode('utf-8')

    def to_dict(self):
        music_str = super(Music, self).to_json()
        music = json.loads(music_str)
        music['music_id'] = str(self.music_id)
        music['music_url'] = self.music_url
        music['img_url'] = self.img_url
        return music

    def update_info(self, music_name, music_artist, music_album):
        self.music_name = music_name
        self.music_artist = music_artist
        self.music_album = music_album
        # self.music_upload_date = datetime.datetime.now()
        self.save()

    def update_file(self, file):
        try:
            self.reload()
            with open(file, 'r') as f:
                self.music_file.replace(f)
                self.save()
        except mongoengine.errors.OperationError:
            pass

    def remove(self):
        self.music_file.delete()
        self.delete()

    def played(self):
        self.music_played += 1
        self.save()

    def vote(self, val):
        try:
            self.music_voted[val] += 1
        except:
            self.music_voted[val] = 1
        self.save()

    def de_vote(self, val):
        if self.music_voted.get(val, None):
            self.music_voted[val] -= 1
        self.save()

    def clean_vote(self):
        self.music_voted = {}
        self.save()

    def gc(self):
        if self.music_upload_user is not None:
            try:
                self.music_upload_user.user_id
            except AttributeError:
                self.music_upload_user = None
                self.save()


class MusicSet(object):
    '''
    Music control functions
    '''

    def __init__(self):
        raise NotImplementedError('MusicSet can\'t be __init__')

    @classmethod
    def add_music(cls, file_name, user_name, remove=False):
        music_name, music_artist, music_album = _get_info_from_id3(file_name)
        user = UserSet.get_user_by_name(user_name)
        music = Music(
            music_name=music_name, music_artist=music_artist,
            music_album=music_album, music_upload_user=user,
            music_upload_date=datetime.datetime.now(),
            music_file=open(file_name, 'r').read()).save()
        from tasks import _lame_mp3
        _lame_mp3.delay(file_name, str(music.music_id), remove)
        # multiprocessing.Process(target=_lame_mp3, args=(file_name, music, remove)).start()
        return music

    @classmethod
    def get_music(cls, music_id):
        try:
            return Music.objects(pk=music_id).first()
        except ValidationError:
            return None

    @classmethod
    def get_all_music(cls):
        return Music.objects()

    @classmethod
    def remove_all_music(cls):
        for music in Music.objects():
            music.remove()

    @classmethod
    def get_next_music(cls):
        assert Music.objects().count() != 0, 'Empty Music List!!'
        return _get_random_music()

    @classmethod
    def get_music_by_name(cls, music_name):
        return Music.objects(music_name=music_name).first()

    @classmethod
    def get_music_by_range(cls, start, end):
        return [each for each in Music.objects[start: end]]

    @classmethod
    def get_music_count(cls):
        return Music.objects().count()

    @classmethod
    def get_music_by_idx(cls, idx):
        return Music.objects[idx]


# def _lame_mp3(infile, music, remove=False):
#     '''
#     lame the mp3 to smaller
#     '''
#     outfile = infile+'.tmp'
#     subprocess.call([
#         "lame",
#         "--quiet",
#         "--mp3input",
#         "--abr",
#         "64",
#         infile,
#         outfile])
#     music.update_file(outfile)
#     os.remove(outfile)

#     if remove:
#         os.remove(infile)


def _get_info_from_id3(file_name):
    # print file_name
    # file_name = file_name.encode('utf8')
    music_name = ''
    music_artist = ''
    music_album = ''

    # os.system('mid3iconv -q -e GBK "%s"' % (file_name))
    argv = ['mid3iconv', '-q', '-e', 'GBK', file_name]
    mid3iconv.main(argv)
    try:
        audio = mutagen.File(file_name, easy=True)
    except:
        print 'On mutagen.File : %s' % (file_name)
        traceback.print_exc()
        return music_name, music_artist, music_album

    # print audio

    try:
        music_name = audio['title'][0]
    except:
        pass

    try:
        music_artist = audio['artist'][0]
    except:
        pass

    try:
        music_album = audio['album'][0]
    except:
        pass

    return music_name, music_artist, music_album


def _get_random_music():
    num = random.randint(0, Music.objects().count()-1)
    return Music.objects[num]


def deduplication():
    music_dict = {}
    for music in MusicSet.get_all_music():
        music_info = music.music_name + music.music_artist + music.music_album
        if music_info in music_dict:
            music_dict[music_info].append(music)
        else:
            music_dict[music_info] = [music]
    for music_info in music_dict:
        if len(music_dict[music_info]) > 1:
            print music_info.encode('utf8'), len(music_dict[music_info])
            for music in music_dict[music_info][:-1]:
                print 'removed', music
                music.remove()

if __name__ == '__main__':
    from master_config import MONGODB_URL, MONGODB_PORT
    connect('miao_fm', host=MONGODB_URL, port=MONGODB_PORT)
    register_connection('miao_fm_cdn', 'miao_fm_cdn', host=MONGODB_URL, port=MONGODB_PORT)

    # try:
    #     MusicSet()
    # except Exception:
    #     pass
    # music = MusicSet.get_music('52526db656a9e5144d800dd5')
    # print music.to_json()
    # print help(Music)
    # print Music.__name__.lower()
    # print dir(music)
    # for each in dir(music):
    #     if each.startswith('music'):
    #         print each

    # list_dirs = os.walk('/media/823E59BF3E59AD43/Music/')
    # for root, dirs, files in list_dirs:
    #     for f in files:
    #         if os.path.join(root, f).endswith('.mp3'):
    #             print os.path.join(root, f)
    #             for each in _get_info_from_id3(os.path.join(root, f)):
    #                 print each.encode('utf8')
    #                 pass
    #             print

    # for each in _get_info_from_id3('/media/823E59BF3E59AD43/Music/mariah carey - without you - 玛丽亚凯莉 失去你.mp3'):
    #     print each

    # MusicSet.add_music('/media/823E59BF3E59AD43/github/python/南拳妈妈 - 小时候.mp3', 'admin')

    # for each in _get_info_from_id3('/media/823E59BF3E59AD43/github/python/刘德华 - 冰雨.mp3'):
    #     print each.encode('utf8')
    # for each in _get_info_from_id3('/media/823E59BF3E59AD43/github/python/南拳妈妈 - 小时候.mp3'):
    #     print each.encode('utf8')
    # for music in MusicSet.get_all_music():
    #     print music.music_upload_user.user_id

    # print MusicSet.add_music('/media/823E59BF3E59AD43/Music/buckle up n chuggeluck heaven.mp3')

    deduplication()
    pass
