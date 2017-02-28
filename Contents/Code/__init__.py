DEBUG = True
API_URL = 'http://josheli-channel-server.dv'

PREFIX = '/video/josheli-tv'
NAME = "Josheli TV"

ART = R('art-default.jpg')
ICON = R('icon-default.jpg')

CHANNEL_ID = 'system'


####################################################################################################
def Start():
    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = NAME
    ObjectContainer.art = ART

    DirectoryObject.thumb = ICON
    VideoClipObject.thumb = ICON
    TrackObject.thumb = ICON

    if DEBUG is False:
        HTTP.CacheTime = CACHE_1HOUR


####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    directory_info = JSON.ObjectFromURL(endpoint(CHANNEL_ID))
    return handle_directory(directory_info)


####################################################################################################
@route(PREFIX + '/handle-directory', directory_info=dict)
def handle_directory(directory_info):

    # probably passed in a channel with items listed
    if 'items' in directory_info:
        directory = directory_info
    else:
        if directory_info['type'] == 'directory':
            endpoint_url = '/directory/' + directory_info['id']
        else:  # channel
            endpoint_url = ''

        directory = JSON.ObjectFromURL(endpoint(directory_info['channel_id'], endpoint_url))

    # if len(directory['items']) < 1:
    #    return ObjectContainer(header=NAME, message="No items were found: " + directory_info['title'])

    oc = ObjectContainer(title1=directory['title'])

    for item in directory['items']:
        if item['type'] == 'directory' or item['type'] == 'channel':
            oc.add(DirectoryObject(key=Callback(handle_directory, directory_info=item),
                                   title=item['title'],
                                   summary=item['summary'],
                                   thumb=Resource.ContentsOfURLWithFallback(item['thumb'], fallback=ICON)))
        elif item['type'] == 'track' or item['type'] == 'video':
            oc.add(create_object(item=item, include_container=False))

    return oc


####################################################################################################
# This function creates an object container for media items
@route(PREFIX + '/create-object', item=dict, include_container=bool)
def create_object(item, include_container=False):

    container = get_container(item)

    # AAC is default for everything but mp3
    if container == 'mp3':
        audio_codec = AudioCodec.MP3
    else:
        audio_codec = AudioCodec.AAC

    if item['type'] == 'track':
        item['container'] = container
        item['audio_codec'] = audio_codec
        new_object = create_audio(item)
    elif item['type'] == 'video':
        new_object = create_video(item)
    else:
        include_container = False
        new_object = DirectoryObject(key=Callback(url_unsupported, title=item['title']),
                                     title="Media Type Not Supported", thumb=R('no-feed.jpg'),
                                     summary='The file %s is not a type currently supported by this channel' % url)

    if include_container:
        return ObjectContainer(objects=[new_object])
    else:
        return new_object


def create_audio(item):

    return TrackObject(
        key=Callback(create_object, item=item, include_container=True),
        rating_key=item['url'],
        title=item['title'],
        summary=item['summary'],
        thumb=Resource.ContentsOfURLWithFallback(item['thumb'], fallback=ICON),
        originally_available_at=Datetime.FromTimestamp(item['date']),
        items=[
            MediaObject(
                parts=[
                    PartObject(key=item['url'])
                ],
                container=item['container'],
                audio_codec=item['audio_codec'],
                audio_channels=2
            )
        ]
    )


def create_video(item):

    return VideoClipObject(
        title=item['title'],
        summary=item['summary'],
        thumb=Resource.ContentsOfURLWithFallback(item['thumb'], fallback=ICON),
        originally_available_at=Datetime.FromTimestamp(item['date']),
        url=item['url']
    )


####################################################################################################
# This function creates an error message for feed entries that have an usupported media type and keeps a section of
# feeds from giving an error for the entire list of entries
@route(PREFIX + '/url-unsupported')
def url_unsupported(title):

    return ObjectContainer(header="Error",
                           message='The media for the %s feed entry is of a type that is not supported' % title)


def get_container(item):

    containers = {
        'avi': Container.AVI,
        'flv': Container.FLV,
        'flash+video': Container.FLV,
        'mp3': 'mp3',
        'mp4': Container.MP4,
        'mpeg4': Container.MP4,
        'h.264': Container.MP4,
        'mkv': Container.MKV,
        'mov': Container.MOV
    }

    if 'container' in item and item['container'].lower() in containers:
        return containers[item['container']]

    url = item['url'].lower()

    for container in containers:
        if url.endswith(container):
            return containers[container]

    return ''


def endpoint(channel_id, resource=''):

    url = API_URL + '/channel/' + channel_id
    if resource != '':
        url += resource
    return url


def log(str):
    if DEBUG:
        Log.Debug(str)
