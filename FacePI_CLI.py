import sys, os, json, time, fire
from PIL import Image
import ClassFaceAPI as FaceAPI
import ClassCamera as Camera
import ClassGTTS, ClassUtils as Utils
from pypinyin import lazy_pinyin

basepath = os.path.dirname(os.path.realpath(__file__))
config = Utils.loadConfig()
personGroupId = config['personGroupId']
api_key = config['api_key']
host = config['host']


class FacePI_CLI:
    ''' FacePI 文字介面
    搭配參數如下：
    buildTraindatas: 三連拍建立圖片資料庫 trainsdata（不進行訓練）
    createPersonGroup: 建立一個 PersonGroup
    config: 列出 Config.json 設定。
    deletePersonGroup: 刪除一個 PersonGroup
    deletePersonInGroup: 刪除 PersonGroup 裡的一個 Person
    identify: 用網路 URL 或本地圖片進行辨識。,
    listPersonGroups: 列出所有的 PersonGroups
    listPersonsInGroup: 列出「人群」裡有哪些 Person
    relay: 設定繼電器,
    status: 觀察 PersonGroup status
    searchPersonName: 搜尋一個personName,
    train: 訓練 PersonGroup
    trainNewPerson: 用 3 連拍訓練一個新人
    trainDatas: '訓練 /traindatas 裡的圖檔，同時訓練一群事先準備好的人與照片',
    Signin: 進行簽到！
    '''

    # 加入一個人的眾多圖片，但不訓練
    def __add_personimages(self, personGroupId, personname, imagepaths):
        print("personname=", personname, "圖檔:", imagepaths)
        personAPI = FaceAPI.Person(api_key, host)
        person = personAPI.getPersonByName(personGroupId, personname)
        if person == None:
            print('call create_a_person')
            personid = personAPI.create_a_person(personGroupId, personname,
                                                 personname + ' 說明。')
            for imagepath in imagepaths:
                personAPI.add_a_person_face(imagepath, personid, personGroupId)
        else:
            print('call add_a_person_face, personId=', person['personId'])
            for imagepath in imagepaths:
                personAPI.add_a_person_face(imagepath, person['personId'],
                                            personGroupId)

    # 將整個 traindatas 的圖片全部送上去訓練
    def __train_traindatas(self, personGroupId):
        traindataPath = basepath + '/traindatas/'
        trainfiles = os.listdir(traindataPath)
        print('目前 traindatas/ 內的圖檔如下：')

        for personname in trainfiles:
            #print("file="+ os.path.join(traindataPath, trainfile))
            personpath = os.path.join(traindataPath, personname)
            if os.path.isdir(personpath):
                print("person name=", personname)
                personImagePaths = []
                for personImagePath in os.listdir(personpath):
                    personImagePaths.append(
                        os.path.join(personpath, personImagePath))
                print(personGroupId, personname, personImagePaths)
                self.__add_personimages(personGroupId, personname,
                                        personImagePaths)
                time.sleep(6)

        personGroupapi = FaceAPI.PersonGroup(api_key, host)
        personGroupapi.train_personGroup(personGroupId)

    def trainNewPerson(self, personname):
        ''' 1. 用 3 連拍訓練一個新人 '''
        #personname = input('進行 3 連拍，請輸入要訓練的對象姓名：')
        traindatasPath = basepath + '/traindatas/'
        jpgimagepaths = []
        for i in range(3):
            jpgimagepath = Camera.takePicture(personGroupId, 2000, size='large')
            #time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()) + ".jpg"
            filename = jpgimagepath[jpgimagepath.rfind('/'):]
            jpgtraindata = '/home/pi/traindatas/' + personname + filename
            if not os.path.exists(os.path.dirname(jpgtraindata)):
                os.makedirs(os.path.dirname(jpgtraindata))
            os.rename(jpgimagepath, jpgtraindata)
            jpgimagepaths.append(jpgtraindata)

        self.__add_personimages(personGroupId, personname, jpgimagepaths)
        personGroupapi = FaceAPI.PersonGroup(api_key, host)
        personGroupapi.train_personGroup(personGroupId)


    def listPersonGroups(self):
        ''' 2: '列出所有的 PersonGroups' '''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        persongroups = PersonGroup.ListPersonGroups()
        if persongroups == None:
            print("讀取 PersonGroup 發生錯誤！: ", persongroups)
            sys.exit()
        if 'error' in persongroups:
            print("讀取 PersonGroup 發生錯誤！: ", persongroups['error']['message'])
            sys.exit()
        print('總共有 ', len(persongroups), '個「人群」')
        for persongroup in persongroups:
            print('personGroupId=' + persongroup['personGroupId'])
            print(persongroup)

    def listPersonsInGroup(self):
        ''' 3: '列出「人群」裡有哪些 Person',        '''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        persons = PersonGroup.list_persons_in_group(personGroupId)
        if len(persons) == 0:
            print('本 personGroupId 內沒有任何一個 person')
            sys.exit()
        for person in persons:
            print('name=' + person['name'] + ':',
                  'personId=' + person['personId'], 'persistedFaceIds=',
                  len(person['persistedFaceIds']))

    def deletePersonGroup(self):
        ''' 4: '刪除某個 PersonGroups','''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        PersonGroup.deletePersonGroup(input('請輸入要刪除的 personGroupId:'))

    def deletePerson(self, personid):
        ''' 5: 刪除 PersonGroup 裡的一個 Person '''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        personApi = FaceAPI.Person(api_key, host)

        # persongroups = PersonGroup.ListPersonGroups()
        # print('總共有 ', len(persongroups), '個「人群」')
        # for persongroup in persongroups:
        #     print('personGroupId=', persongroup)
        #personGroupId = input('請輸入 personGroupId: ')
        persons = PersonGroup.list_persons_in_group(personGroupId)
        for person in persons:
            print('name=' + person['name'] + ':', person)
        #personid = input('請輸入將要刪除的 personid: ')
        personApi.deletePerson(personGroupId, personid)

    def status(self):
        ''' 7: 觀察 PersonGroup status '''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        PersonGroup.personGroup_status(personGroupId)

    def train(self):
        ''' 8: 訓練 PersonGroup '''
        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        PersonGroup.train_personGroup(personGroupId)

    def createPersonGroup(self, personGroupName):
        ''' 9: 建立一個 PersonGroup '''
        # personGroupName = input('請輸入 personGroup name(可用中文): ')
        personGroupId = '_'.join(lazy_pinyin(personGroupName))

        PersonGroup = FaceAPI.PersonGroup(api_key, host)
        PersonGroup.createPersonGroup(personGroupId, personGroupName,
                                      'group userdata')

    def config(self):
        ''' 10: 列出 Config.json 設定。 '''
        api_key = input('請輸入有效的 API KEY[' + config['api_key'] + ']:')
        if api_key != '':
            config['api_key'] = api_key
        host = input("驗證主機[" + config['host'] + "]: ")
        if host != '':
            config['host'] = host
        camera = input("攝影機[" + config['camera'] + "]: ")
        if camera != '':
            config['camera'] = camera
        title = input("自訂標題[" + config['title'] + "]：")
        if title != '':
            config['title'] = title
        with open(basepath + '/Config.json', 'w', encoding='utf-8') as outfile:
            json.dump(config, outfile, ensure_ascii=False)

    def trainDatas(self):
        ''' 11: '訓練 /traindatas 裡的圖檔，同時訓練一群事先準備好的人與照片 '''
        self.__train_traindatas(personGroupId)

    def searchPersonName(self, personname):
        ''' 12: 搜尋 PersonGroup 裡的 personName '''
        #personname = input('請輸入要找尋的 personname: ')
        personApi = FaceAPI.Person(api_key, host)
        persons = personApi.getPersonsByName(personGroupId, personname)
        for person in persons:
            print("person: ", person)

    def relay(self):
        ''' 13: '設定繼電器 '''
        #ClassGPIO.RelayExchange()
        print('call ClassGPIO.RelayExchange()')

    def identify(self, imageurl):
        ''' 14: 準備要辨識的 image URL or 檔案路徑 '''
        start = int(round(time.time() * 1000))
        print('開始計時 identify')
        faceApi = FaceAPI.Face(api_key, host)
        personApi = FaceAPI.Person(api_key, host)
        print('載入 class', int(round(time.time() * 1000)-start), 'ms')
        #imageurl = input('請輸入準備要辨識的 image URL or 檔案路徑:')
        if imageurl.startswith('http'):
            imageurls = []
            imageurls.append(imageurl)
            detectfaces = faceApi.detectURLImages(imageurls)
        else:
            print('SPEED: localimage', int(round(time.time() * 1000)-start), 'ms')
            imageurl = imageurl.strip()
            statinfo = os.stat(imageurl)
            print('檔案大小：', statinfo.st_size, 'Bytes')
            if statinfo.st_size < 1024:
                print('圖檔太小 不可小於 1KB')
                sys.exit(1)
            elif statinfo.st_size > 4 * 1024 * 1024:
                print('圖檔太大 不可大於 4MB')
                im = Image.open(imageurl)
                out = im.resize((128, 128))
                im.save(imageurl, "JPEG")
                print('out=', type(out))
            print('SPEED: detectLocalImage前', int(round(time.time() * 1000)-start), 'ms')
            detectfaces = faceApi.detectLocalImage(imageurl)
            print('SPEED: detectLocalImage後', int(round(time.time() * 1000)-start), 'ms')

        if len(detectfaces) == 0:
            print('相片中找不到人！')
            sys.exit(1)

        faceids = []
        for face in detectfaces:
            print('所偵測到的 faceId=', face['faceId'])
            faceids.append(face['faceId'])

        print('SPEED: faceApi.identify 前', int(round(time.time() * 1000)-start), 'ms')
        identifyfaces = faceApi.identify(faceids[:10], personGroupId)
        print('SPEED: faceApi.identify 後', int(round(time.time() * 1000)-start), 'ms')
        print('在所提供的相片中偵測到 identifyfaces 共 ', len(identifyfaces), '個',
              identifyfaces)
        for identifyface in identifyfaces:
            # print('candidateface 的[\'candidates\'] 其中有 ',
            #       len(candidateface['candidates']), '個在辨認資料庫內')
            for candidate in identifyface['candidates']:
                personId = candidate["personId"]
                confidence = candidate["confidence"]
                # print('辨認候選人 candidate: personId=', personId, confidence,
                #       candidate)
                person = personApi.get_a_person(personId, personGroupId)
                #print(person['name'],
                #      '簽到成功（' + str(confidence) + '）！', person['personId'],
                #      len(person['persistedFaceIds']), '個 faceid')
                print('SPEED: play_gTTS 前', int(round(time.time() * 1000)-start), 'ms')
                ClassGTTS.play_gTTS(person['name'], '簽到成功')
                print('SPEED: play_gTTS 後', int(round(time.time() * 1000)-start), 'ms')

    def buildTraindatas(self, personname):
        ''' 15: '快速 3 連拍建立圖片資料庫不進行訓練） '''
        personname = input('進行 3 連拍，請輸入姓名(儲存不訓練)：')
        # 建檔先暫放 /tmp 以免更新程式被清除。
        traindatasPath = '~/traindatas/' + personname + "/"
        if not os.path.exists(os.path.dirname(traindatasPath)):
            os.makedirs(os.path.dirname(traindatasPath))

        jpgimagepaths = []
        for i in range(3):
            jpgimagepath = Camera.takePicture(personGroupId, 2000, size='large')
            index = jpgimagepath.rfind('/')
            os.rename(jpgimagepath, traindatasPath + jpgimagepath[index:])
            #time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()) + ".jpg"
            # jpgimagepaths.append(jpgimagepath)

    def Signin(self):
        ''' 簽到！ '''
        start = int(round(time.time() * 1000))
        print('開始計時 Sign', start, 'ms')
        jpgimagepath = Camera.takePicture(personGroupId, 2000)
        print('Signin: 拍照後', int(round(time.time() * 1000))-start,'ms')
        self.identify(jpgimagepath)
        print('Signin 辨識後', int(round(time.time() * 1000))-start,'ms')

if __name__ == '__main__':
    fire.Fire(FacePI_CLI)
