import sys
import json
import pytest
sys.path.append('/home/pi/projects/px1/')
import memesocial


@pytest.fixture
def client(request):
    client = memesocial.app.test_client()

    def teardown():
        memesocial.db.drop_tables(memesocial.all_tables)
        memesocial.db.create_tables(memesocial.all_tables)
    request.addfinalizer(teardown)
    return client


def register_user(client, username, password):
    """
    test user register endopoint
    """
    response = client.post(
        '/api/register_user',
        data=json.dumps({
            'username': username,
            'password': password
        }),
        content_type='application/json'
    )
    assert response.status_code == 200


def get_users(client):
    response = client.get('/api/user/1')
    assert response.data == ''


def do_login(client, username='mohamed', password='123'):
    """
    Just login
    """
    response = client.post(
        '/api/login',
        data=json.dumps({
            'username': username,
            'password': password
        }),
        content_type='application/json'
    )
    return response.status_code


def do_logout(client):
    return client.get('/api/logout').status_code


def update_profile_image(client, imageName):
    response = client.post(
        '/api/update_profile_image',
        data=open(imageName, 'r').read(),
        content_type='application/octet-stream'
    )
    return response.status_code


def update_cover_image(client, imageName):
    response = client.post(
        '/api/update_cover_image',
        data=open(imageName, 'r').read(),
        content_type='application/octet-stream'
    )
    return response.status_code


def mk_content(client, imageName, description):
    import base64
    response = client.post(
        '/api/create_content',
        data=json.dumps({
            'desc': description,
            'image': base64.b64encode(open(imageName, 'r').read())
        }),
        content_type='application/json',
    )
    return (response.status_code, json.loads(response.data))


def test_hello_world(client):
    # just to test if my config works
    assert client.get('/api/hello').data == 'Hello Mohamed'


def test_auth_system(client):
    """
    test authentifcation system, login/register n logout
    """
    register_user(client, 'mohamed', '123')
    assert do_login(client) == 200
    assert do_logout(client) == 200


def test_change_images(client):
    register_user(client, 'mohamed', '123')
    do_login(client)
    assert update_cover_image(client, 'imgTest.jpg') == 200
    assert update_profile_image(client, 'imgTest.jpg') == 200


def heart_content(client, cid):
    response = client.get(
        '/api/heartit/%i' % cid,
    )
    return response.status_code


def unheart_content(client, cid):
    response = client.get(
        '/api/unheartit/%i' % cid
    )
    return response.status_code


def get_content(client, cid):
    response = client.get(
        '/api/content/%i' % cid
    )
    return response.status_code, json.loads(response.data)


def test_content(client):
    """
    make content heart it and unheart it test
    """

    # make new users for this
    register_user(client, 'mohamed', '123')
    register_user(client, 'gauss', 'motherfucker')
    do_login(client)
    # make content
    r = mk_content(client, 'imgTest.jpg', 'LOL')
    assert r[0] == 200
    assert 'success' in r[1]
    assert 'contentid' in r[1]['success'][0]
    cid = r[1]['success'][0]['contentid']
    assert heart_content(client, cid) == 200
    do_logout(client)

    print 'This shall be gauss'
    assert do_login(client, username='gauss', password='motherfucker') == 200

    assert client.get('/api/whoami').data == '2'

    assert heart_content(client, cid) == 200
    r = get_content(client, cid)
    assert r[0] == 200
    assert 'success' in r[1]
    assert len(r[1]['success'][0]['hearters']) == 2

    # test unheart
    assert unheart_content(client, cid) == 200
    # test unheart already unhearted
    assert unheart_content(client, cid) == 202

    # see if unhearted ?
    r = get_content(client, cid)
    assert r[0] == 200
    assert 'success' in r[1]
    assert len(r[1]['success'][0]['hearters']) == 1


def do_follow(client, user, password, target):
    do_login(client, user, password)
    assert client.get('/api/follow/%i' % target).status_code == 200
    do_logout(client)


def do_comment(client, contentId, commentContent):
    response = client.post(
        '/api/comment',
        data=json.dumps({
            'content_id': contentId,
            'comment_content': commentContent
        }),
        content_type='application/json'
    )
    return response.status_code


def test_comment(client):
    register_user(client, 'mohamed', '123')
    register_user(client, 'gauss', 'motherfucker')
    do_login(client, username='mohamed', password='123')
    assert mk_content(client, 'imgTest.jpg', 'Yay funny meme')[0] == 200
    do_logout(client)
    do_login(client, username='gauss', password='motherfucker')
    assert do_comment(client, 1, 'Really funny lol') == 200
    rv = get_content(client, 1)
    assert rv[0] == 200
    assert len(rv[1]['success'][0]['commentors']) == 1

    # test of comment on content that does not exist
    assert do_comment(client, 97, 'Fuck all you') == 404


def test_network(client):
    """
    Keyword Arguments:
    client -- client callback
    What will this do is test the follow system, and test my suggestion leaders suggestion algorithms
    """
    register_user(client, 'mohamed', '123')
    register_user(client, 'gauss', 'motherfucker')
    register_user(client, 'euler', 'mathisCool')
    register_user(client, 'unk', 'unk')
    register_user(client, 'test', 'test')
    register_user(client, 'gi', 'pi')
    # this should not be in outside of the local network
    register_user(client, 'Ha', 'pa')
    register_user(client, 'Cha', 'pa')

    # building a simple follow network
    do_follow(client, 'mohamed', '123', 2)
    do_follow(client, 'mohamed', '123', 3)

    do_follow(client, 'gauss', 'motherfucker', 4)

    do_follow(client, 'euler', 'mathisCool', 2)
    do_follow(client, 'euler', 'mathisCool', 1)

    do_follow(client, 'gi', 'pi', 1)
    do_follow(client, 'gi', 'pi', 3)
    do_follow(client, 'gi', 'pi', 5)

    do_follow(client, 'test', 'test', 1)

    # shall be outside of the network
    do_follow(client, 'Ha', 'pa', 8)
    do_follow(client, 'Cha', 'pa', 7)

    do_login(client, username='mohamed', password='123')

    # my tests for now
    assert json.loads(client.get('/api/maybe_like').data) == {u'4': 0.6127450980392157, u'5': 0.1830065359477124, u'6': 0.14215686274509803}


def test_meme_feed(client):
    """
    Keyword Arguments:
    client -- the client callback function
    """
    pass
