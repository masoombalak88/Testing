#
# Copyright (C) 2024-present by TeamYukki@Github, < https://github.com/TeamYukki >.
#
# This file is part of < https://github.com/TeamYukki/YukkiMusicBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiMusicBot/blob/master/LICENSE >
#
# All rights reserved.
#


import sys
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters
import random
import re

load_dotenv()

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

votemode = {}

confirmer = {}

def seconds_to_time(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"
    
XYZ = [
    "https://telegra.ph/file/aaccc060f01052d8b0c56.jpg",
    "https://telegra.ph/file/f95ccd8e2a848997aaecb.jpg",
    "https://telegra.ph/file/e2e83fbcab3b31be1c3ce.jpg",
    "https://telegra.ph/file/bac90d63af198e41cffb6.jpg",
    "https://telegra.ph/file/3430c656f7d401187aef9.jpg",
    "https://telegra.ph/file/3b90c6873a5ce7508874c.jpg",
    "https://telegra.ph/file/90aebcc77e667f2c4370e.jpg",
    "https://telegra.ph/file/0d9c50f00f8300dcb95bf.jpg",
    "https://telegra.ph/file/b5b4546e88f8e99b946f9.jpg",
    "https://telegra.ph/file/1c50855ed48d476db38b9.jpg",
    "https://telegra.ph/file/30f5a4879ef30cbaf570b.jpg",
    "https://telegra.ph/file/018ae93db9fc559037cca.jpg",
    "https://telegra.ph/file/7569a9bc7b1a15486d746.jpg",
    "https://telegra.ph/file/40ba771bd9bb09d8c3074.jpg",
    "https://telegra.ph/file/8236f9065052b64ff2e88.jpg",
    "https://telegra.ph/file/bedb48e5b60e851db76ab.jpg",
    "https://telegra.ph/file/0ea5ce00d861e3d9ac58b.jpg",
    "https://telegra.ph/file/a35fc589e2e18e23cec45.jpg",
    "https://telegra.ph/file/35cf616aff899af0ee1a8.jpg",
    "https://telegra.ph/file/c621138c96d31ea0f52f7.jpg",
    "https://telegra.ph/file/e936df1516f652c69012e.jpg",
    "https://telegra.ph/file/faf95efda558dfa7fc71b.jpg",
    "https://telegra.ph/file/eee29579be2e002f2a0a5.jpg",
    "https://telegra.ph/file/cf1d61e2cefb43aa94012.jpg",
    "https://telegra.ph/file/0443c6e441f9d9051aeff.jpg",
    "https://telegra.ph/file/729569d36b6f0f0de56cb.jpg",
    "https://telegra.ph/file/ec1c958c99bd005dce54a.jpg",
    "https://telegra.ph/file/c85ec1fac5caf9d46ab38.jpg",
    "https://telegra.ph/file/0be319beef16edf0030d8.jpg",
    "https://telegra.ph/file/c6adab3ebbfe404da751a.jpg",
    "https://telegra.ph/file/623b560c96188f566e740.jpg",
    "https://telegra.ph/file/018ae93db9fc559037cca.jpg",
    "https://telegra.ph/file/1c50855ed48d476db38b9.jpg",
    "https://telegra.ph/file/b5b4546e88f8e99b946f9.jpg",
    "https://telegra.ph/file/0d9c50f00f8300dcb95bf.jpg",
    "https://telegra.ph/file/3b90c6873a5ce7508874c.jpg",
    "https://telegra.ph/file/bac90d63af198e41cffb6.jpg",
    "https://telegra.ph/file/90aebcc77e667f2c4370e.jpg",
    "https://telegra.ph/file/3430c656f7d401187aef9.jpg",
    "https://telegra.ph/file/aaccc060f01052d8b0c56.jpg",
    "https://telegra.ph/file/e2e83fbcab3b31be1c3ce.jpg",
    "https://telegra.ph/file/a014646b47dec5330df0b.jpg",
    "https://telegra.ph/file/8a76657c5328b74539e3f.jpg",
    "https://telegra.ph/file/32f0afd470c5b95d8caef.jpg",
    "https://telegra.ph/file/6b1456ae99751f2faf232.jpg",
    "https://telegra.ph/file/e57579a301ec51e4e3291.jpg",
    "https://telegra.ph/file/ae4d91434aac3e8c16c4e.jpg",
    "https://telegra.ph/file/dc23af04fd9fe0e71e9bf.jpg",
    "https://telegra.ph/file/95fc275938a4b844f4949.jpg",
    "https://telegra.ph/file/8548e8ffbb636060fb957.jpg",
    "https://telegra.ph/file/5c484fa1e8c2054d3049a.jpg",
    "https://telegra.ph/file/4af74d0b967c74e7cb03e.jpg",
    "https://telegra.ph/file/175ccf7c3a9cc64662e47.jpg",
    "https://telegra.ph/file/9e3b4039b1d6630a8c1a2.jpg",
    "https://telegra.ph/file/f549a49b3cd3ce9bfea45.jpg",
    "https://telegra.ph/file/d38beb3076abf271cf5b8.jpg",
    "https://telegra.ph/file/a3f93696a84575100bde9.jpg",
    "https://telegra.ph/file/91a4faa72dd54641c09c8.jpg",
    "https://telegra.ph/file/0d2e8149591754d665198.jpg",
    "https://telegra.ph/file/d0217d33a6276a398db2f.jpg",
    "https://telegra.ph/file/b39da05abc9aa42bff8fc.jpg",
    "https://telegra.ph/file/551a9d50ce04bd1637368.jpg",
    "https://telegra.ph/file/b86f07a90f00623cf7973.jpg",
]

Zero = [
    "https://telegra.ph/file/59b9696f98fc9801fb8a3.jpg",
    "https://telegra.ph/file/40ee2fea655fdaccb5676.jpg",
    "https://telegra.ph/file/2bf0a9e96e05c3b885f3e.jpg",
    "https://telegra.ph/file/748ab35ba5505941179d2.jpg",
    "https://telegra.ph/file/e3d517baa16d4d9175a63.jpg",
    "https://telegra.ph/file/31c761b649870cf244c68.jpg",
    "https://telegra.ph/file/ee33e0e9eb06f455fd8b8.jpg",
    "https://telegra.ph/file/5b647d2cb8ea742c14812.jpg",
    "https://telegra.ph/file/7d340e518b0503b7321e5.jpg",
    "https://telegra.ph/file/a1a2d523241d6dded6f81.jpg",
    "https://telegra.ph/file/3aa90e94a5601828a27b6.jpg",
    "https://telegra.ph/file/9e0f6ae4387667a40e4b1.jpg",
    "https://telegra.ph/file/53f6c0c089bebbb357d38.jpg",
    "https://telegra.ph/file/8cea94bf7e503531a3078.jpg",
    "https://telegra.ph/file/e2ae762e328636eb8277f.jpg",
    "https://telegra.ph/file/7a022c585f16ac3da9ca3.jpg",
    "https://telegra.ph/file/c618a8184593b89d97cac.jpg",
    "https://telegra.ph/file/f1fb515a11adf36a9d453.jpg",
    "https://telegra.ph/file/36a63da50dcc4943053db.jpg",
    "https://telegra.ph/file/4ee948352d7ea883904b2.jpg",
    "https://telegra.ph/file/5e715d363451474df62dd.jpg",
    "https://telegra.ph/file/6634462797341a1103e16.jpg",
    "https://telegra.ph/file/35a5c2d74e952a4ab91d3.jpg",
    "https://telegra.ph/file/4de8c34ef817b3c43b3a4.jpg",
    "https://telegra.ph/file/d1248deeabe5faa685c76.jpg",
    "https://telegra.ph/file/7ec14065c10886c21a460.jpg",
    "https://telegra.ph/file/5abf4bb5393629189d614.jpg",
    "https://telegra.ph/file/a88a5d73a122697938db3.jpg",
    "https://telegra.ph/file/a93939ff17aa2b344910d.jpg",
    "https://telegra.ph/file/5eaddf49d259af1546ec4.jpg",
    "https://telegra.ph/file/b53ab37579a42d5c504c3.jpg",
    "https://telegra.ph/file/398f82cc9965d27176d6f.jpg",
    "https://telegra.ph/file/73fb5f935ba47ecbede4b.jpg",
    "https://telegra.ph/file/db467cee76f37a490e4a0.jpg",
    "https://telegra.ph/file/ae5da8d0d1f8431dd5b51.jpg",
    "https://telegra.ph/file/80ca183c61fb91269c8b5.jpg",
    "https://telegra.ph/file/13dbe7df77791e9bd80c4.jpg",
    "https://telegra.ph/file/31bb5024d8e32a4333f87.jpg",
    "https://telegra.ph/file/57184799373eeeebfddce.jpg",
    "https://telegra.ph/file/098156c5d16866da0f5a8.jpg",
    "https://telegra.ph/file/be82723050edf998bd556.jpg",
    "https://telegra.ph/file/150f49bdd93181d2bc78f.jpg",
    "https://telegra.ph/file/f1d31ba99dd51e2e70481.jpg",
    "https://telegra.ph/file/0440b100868614d707b3c.jpg",
    "https://telegra.ph/file/d9dc7dba5eac897a33f47.jpg",
    "https://telegra.ph/file/9a83642458467be2df04a.jpg",
    "https://telegra.ph/file/c3eb7b4e06ff10d8a4694.jpg",
    "https://telegra.ph/file/eb83cef2a0806c97d4c0a.jpg",
    "https://telegra.ph/file/bbeb88cf6a25ed4071425.jpg",
    "https://telegra.ph/file/d62f7a27dfb73f8874f9a.jpg",
    "https://telegra.ph/file/127946a2d68030c67e945.jpg",
    "https://telegra.ph/file/779657a60dc3ebd930b80.jpg",
    "https://telegra.ph/file/4daa8ddd88b90fb99e96f.jpg",
    "https://telegra.ph/file/5ded4b7339e922f1fb25b.jpg",
    "https://telegra.ph/file/2496b1790c2c70c5598a4.jpg",
    "https://telegra.ph/file/eb0a57874ff169b94547e.jpg",
    "https://telegra.ph/file/b012ca4267d37001edaf4.jpg",
    "https://telegra.ph/file/b05221b0fc463abafbdfa.jpg",
    "https://telegra.ph/file/fee03ce28f6e426a1ccd7.jpg",
    "https://telegra.ph/file/1b1af538e96ec6d57a9eb.jpg",
    "https://telegra.ph/file/1a58f0ffcc50272d13d5a.jpg",
    "https://telegra.ph/file/261b94f61e387dffce19f.jpg",
    "https://telegra.ph/file/16e0eec0864b00a70d8d4.jpg",
    "https://telegra.ph/file/aaa11bac1f2b410259bdf.jpg",
    "https://telegra.ph/file/c75f04959e0b9d1f620af.jpg",
    "https://telegra.ph/file/5451cbac593d7e758b445.jpg",
    "https://telegra.ph/file/6a8a94833d568ea4b8bcb.jpg",
    "https://telegra.ph/file/834a8edd1f1169a9e4ff5.jpg",
    "https://telegra.ph/file/0970704ed7fb1be6e93f4.jpg",
    "https://telegra.ph/file/260e9b13a7560cf5980fa.jpg",
    "https://telegra.ph/file/bcc3c17be9b5073220217.jpg",
    "https://telegra.ph/file/4048ea8ec78276ab27eed.jpg",
    "https://telegra.ph/file/db08b3f97954172dde1b0.jpg",
    "https://telegra.ph/file/6c775cdb7eccbdb02766e.jpg",
    "https://telegra.ph/file/64e81bfbf58877eb4b914.jpg",
    "https://telegra.ph/file/7171044ffc9b0c7e328ce.jpg",
    "https://telegra.ph/file/3a9d343970db017d13490.jpg",
    "https://telegra.ph/file/39a46d232cd38746cb370.jpg",
    "https://telegra.ph/file/0ca48d870c7fbbe876cbf.jpg",
    "https://telegra.ph/file/7611d7f596e434dd5d7d2.jpg",
    "https://telegra.ph/file/a7c0df8d2c673afd5cb4a.jpg",
    "https://telegra.ph/file/5c495f44be4b1d21035ad.jpg",
    "https://telegra.ph/file/d28d9e38fae3bbfa54bfe.jpg",
    "https://telegra.ph/file/a4bce308f3d0b9c050aa4.jpg",
    "https://telegra.ph/file/e3ee09d8abceac61f3d03.jpg",
    "https://telegra.ph/file/ee1473eb244d34ec67d83.jpg",
    "https://telegra.ph/file/9a450ea8ab11630ffa023.jpg",
    "https://telegra.ph/file/fbd2df5fbb24d11658ce3.jpg",
    "https://telegra.ph/file/79f9c73a5786336dc2cb7.jpg",
    "https://telegra.ph/file/b0ccd3f20f76e1e242ce0.jpg",
    "https://telegra.ph/file/c32a0938308519f086b0d.jpg",
    "https://telegra.ph/file/78ad2a6550131881ef99d.jpg",
    "https://telegra.ph/file/de792f69b71a2cc61dedd.jpg",
    "https://telegra.ph/file/e0ab1d8e477118ccf1131.jpg",
    "https://telegra.ph/file/1ab0005517a31e23e593d.jpg",
]

RANDOMIMG = ["https://telegra.ph/file/c777a8fba33ea23e20f02.jpg","https://telegra.ph/file/eb2a1b5875dbd87ad16b5.jpg","https://telegra.ph/file/eb360fb4e80d7bb08b941.jpg","https://telegra.ph/file/4f5d1d86be0a8b5e7d81d.jpg","https://telegra.ph/file/eceb13fc17b0150aa9cea.jpg","https://telegra.ph/file/6f3a8b5643d0ca82bd1f6.jpg","https://telegra.ph/file/9a12a9d6a9fea986f2ec7.jpg","https://telegra.ph/file/5d95a16a2ad07f59d1074.jpg","https://telegra.ph/file/4b6bd810600733e53d929.jpg","https://telegra.ph/file/4a2e606b2f6d02bf61cb7.jpg","https://telegra.ph/file/c9c2969b16e86552f5b55.jpg","https://telegra.ph/file/d8a1aa350aa7d93e66d82.jpg","https://telegra.ph/file/904140188f9b0fc489590.jpg","https://telegra.ph/file/42adebe71fa4257f39b75.jpg","https://telegra.ph/file/0be9952c86295cb8f78db.jpg","https://telegra.ph/file/9036592c9f9b7b6bbc08a.jpg","https://telegra.ph/file/f14e9ba47831e5c82749f.jpg","https://telegra.ph/file/a0ef1ac59c6a1d104da96.jpg","https://telegra.ph/file/5e678d026ab7a6ac1922b.jpg","https://telegra.ph/file/0946bc125e890361ae2c2.jpg","https://telegra.ph/file/e35abc8996bb0fab9aa48.jpg","https://telegra.ph/file/997baa16121e0455acfad.jpg","https://telegra.ph/file/43a1f6a3fd4f9508ed5e3.jpg","https://telegra.ph/file/9377dbd1bdcf6b2f8d5dc.jpg","https://telegra.ph/file/5c02f2f3bd91ef1ccda66.jpg","https://telegra.ph/file/4f1d1437891ccc80812bf.jpg","https://telegra.ph/file/06e3a538771d6fd7f0a9a.jpg","https://telegra.ph/file/b583bcce2c335319ba368.jpg","https://telegra.ph/file/d6b80d241d4b329426452.jpg","https://telegra.ph/file/e4be7ef8a4f9acb9afc89.jpg","https://telegra.ph/file/5dc8d5be84911a0fca74c.jpg","https://telegra.ph/file/94f4ec81a1ea567eda83d.jpg","https://telegra.ph/file/3ef00db7ff5e15c8efc54.jpg","https://telegra.ph/file/22d56cf312248f4fa6489.jpg","https://telegra.ph/file/f5b2ba114aa8d8bb902db.jpg","https://telegra.ph/file/6dad71099a13379f2068d.jpg","https://telegra.ph/file/683959013c0a4c93acbd9.jpg","https://telegra.ph/file/be98dea07f4b5938a4490.jpg","https://telegra.ph/file/becb2d28b38bffd33f6ca.jpg","https://telegra.ph/file/f3bfe1068542aeaa5fd7c.jpg","https://telegra.ph/file/fe4c74858d288d5c61e65.jpg","https://telegra.ph/file/a6ee40f2a954fdac9cb18.jpg","https://telegra.ph/file/86ee02ba743844f861333.jpg","https://telegra.ph/file/158353fb837ca6ee8a77e.jpg","https://telegra.ph/file/9bf45ac99de2417e76bad.jpg","https://telegra.ph/file/72268e50261c5b9667f59.jpg","https://telegra.ph/file/90a3d8099817f471e66fe.jpg","https://telegra.ph/file/d6e53e25328d168eb37b7.jpg","https://telegra.ph/file/fda43826dded3e4738a9e.jpg","https://telegra.ph/file/77243a965fb002157c3f8.jpg","https://telegra.ph/file/9650e40e47e766cd81e35.jpg","https://telegra.ph/file/481a75960ca5d23f1db16.jpg","https://telegra.ph/file/a9ce7ce4258279cfbff31.jpg","https://telegra.ph/file/990bae958f00140b8ee2c.jpg","https://telegra.ph/file/02b80a77aaa39d88b2c79.jpg","https://telegra.ph/file/6c885935e50762da25472.jpg","https://telegra.ph/file/bf8ea432e132ec30cb0c2.jpg","https://telegra.ph/file/30250b09029076698e4b2.jpg","https://telegra.ph/file/bce5cfde2ed72fe655e69.jpg","https://telegra.ph/file/92f3de73c8a0c541dd672.jpg","https://telegra.ph/file/7145ff6c8877f27bf64ca.jpg","https://telegra.ph/file/d82e218980ec409672c68.jpg","https://telegra.ph/file/43693df3a30172b954632.jpg","https://telegra.ph/file/30b92f86ea0a712f4d0ed.jpg","https://telegra.ph/file/8cc5b6fe5a047a1ce1cbd.jpg","https://telegra.ph/file/e2c2fb24469b1b19a0866.jpg","https://telegra.ph/file/46b596a04f9db8041a9d1.jpg","https://telegra.ph/file/549ad9de7da164636e201.jpg","https://telegra.ph/file/2eb793749061146a6037c.jpg","https://telegra.ph/file/7ce0ef5e9216273b8bc27.jpg","https://telegra.ph/file/66a8e54145c27468f0c69.jpg","https://telegra.ph/file/da416ecfcc3e50973172e.jpg","https://telegra.ph/file/0708854fe104da9e1445e.jpg","https://telegra.ph/file/48aa2e6b48a32efaf7017.jpg","https://telegra.ph/file/920b88f2d2b0ccb4e648c.jpg","https://telegra.ph/file/fda8146fd6b22f9637733.jpg","https://telegra.ph/file/5417d79b1eea8d122008f.jpg","https://telegra.ph/file/a43806329815ecc6c2aa3.jpg","https://telegra.ph/file/7c4bf50287cc170d167c4.jpg","https://telegra.ph/file/4d0230d9ed3bf635c712a.jpg","https://telegra.ph/file/e2f9e93ba5af08a7930da.jpg","https://telegra.ph/file/60a2c14dadf79cd394d59.jpg","https://telegra.ph/file/2c564f940bf888aff4721.jpg","https://telegra.ph/file/4ba7e7a4c99f29fad2fb8.jpg","https://telegra.ph/file/912a1496be6da2e021a9a.jpg","https://telegra.ph/file/9a8ecf040565f18b480e4.jpg","https://telegra.ph/file/4b637281b81d3f637f643.jpg","https://telegra.ph/file/02fa944693f8fbcddbdde.jpg","https://telegra.ph/file/393d12eb83a47a0499312.jpg","https://telegra.ph/file/4899608b9d4efeb30ab3d.jpg","https://telegra.ph/file/3992f6c841bbeadad51c2.jpg","https://telegra.ph/file/31c70758a9f35665ee769.jpg","https://telegra.ph/file/d1a1932b2d0d3085c3e8c.jpg","https://telegra.ph/file/cb13f1b053b99afde7b6e.jpg","https://telegra.ph/file/21bc78f527468bc17974f.jpg","https://telegra.ph/file/fc95ab764d7d0ae09871b.jpg","https://telegra.ph/file/7461718da28a92be0e915.jpg","https://telegra.ph/file/9a00595a3a9c50d6d0417.jpg","https://telegra.ph/file/c07a4c967a8d1b74b7937.jpg","https://telegra.ph/file/05e66ebc81a2d4b545011.jpg","https://telegra.ph/file/8b99f321f1d2c04e7e070.jpg","https://telegra.ph/file/76d453ce911a26cd5d2c1.jpg","https://telegra.ph/file/4bc2491037c2b5e67d19f.jpg","https://telegra.ph/file/2203396db0c56a4a5a26e.jpg","https://telegra.ph/file/4dd18dc083d94fdf2b9f3.jpg","https://telegra.ph/file/8ad07af912c0d10445b38.jpg","https://telegra.ph/file/f96f524df10a61e0e3441.jpg","https://telegra.ph/file/11ef6ff8ef6a9ff8e0b28.jpg","https://telegra.ph/file/f92b2d170fb7a1b324da6.jpg","https://telegra.ph/file/b4b5e6c2b6b1571c8b202.jpg","https://telegra.ph/file/292c7ed92b8b6f2a05938.jpg","https://telegra.ph/file/563d14ae81d02b69e403b.jpg","https://telegra.ph/file/52557ff0a356ad90b0df0.jpg","https://telegra.ph/file/2705c40003a49da25f9d7.jpg","https://telegra.ph/file/5e618d003f40a9eea8826.jpg","https://telegra.ph/file/d555a6cb52d0c69c18b80.jpg","https://telegra.ph/file/1568d728f95e4cc7649e6.jpg","https://telegra.ph/file/ee59c2115f10b77eec04e.jpg","https://telegra.ph/file/cb3400b59354d3917a540.jpg","https://telegra.ph/file/ce6f69e98251a8c929bd8.jpg","https://telegra.ph/file/867456e9ba83a4988b020.jpg","https://telegra.ph/file/fafad841229f83fe0cdd4.jpg","https://telegra.ph/file/5378b26aeab101747e80f.jpg","https://telegra.ph/file/0eb5d8b82e4d5a34b7cb8.jpg","https://telegra.ph/file/1d2bff1f515a8a9137267.jpg","https://telegra.ph/file/2835355c0f265a05d1b85.jpg","https://telegra.ph/file/1678d68ff4fa6cdb8479e.jpg","https://telegra.ph/file/1ed45a4b6f019234106ec.jpg","https://telegra.ph/file/3e268fc172bc36273b8a5.jpg","https://telegra.ph/file/61a5097d674e1d08430fc.jpg","https://telegra.ph/file/3df107b48c5a03571110c.jpg","https://telegra.ph/file/39ef20f203c6b038b70e2.jpg","https://telegra.ph/file/511e9184e27c2b7eab420.jpg","https://telegra.ph/file/122703b999ebff4a0df9d.jpg","https://telegra.ph/file/30457fd55198b5b2e1f1f.jpg","https://telegra.ph/file/8d18336a635f511c7b09e.jpg","https://telegra.ph/file/689c0e8d963f0da95c6b8.jpg","https://telegra.ph/file/fe7fc8351b132f6a58755.jpg","https://telegra.ph/file/9e17f6e9b9f98ad9136be.jpg","https://telegra.ph/file/4f832d52e1093d1d618c2.jpg","https://telegra.ph/file/b6469a234fd250b1120ef.jpg","https://telegra.ph/file/97b92f4807e5b918388f3.jpg","https://telegra.ph/file/15b785d64a7a0f46891b7.jpg","https://telegra.ph/file/3dbf4fa1bc2b79b5b746b.jpg","https://telegra.ph/file/758f366c2c1dbec0e29c4.jpg","https://telegra.ph/file/12c7ad36af1131271f5a0.jpg","https://telegra.ph/file/961c2182274a5084e5cf0.jpg","https://telegra.ph/file/3eb2479b00f8c8f133f92.jpg","https://telegra.ph/file/1dd223e881133cc805b43.jpg","https://telegra.ph/file/56d288bb683218176bb4b.jpg","https://telegra.ph/file/05dd16ff17ad40eb4f2bb.jpg"]

MARIN = ["https://telegra.ph/file/1442156ffea729eafc5a2.jpg", "https://telegra.ph/file/7edfdc57f89f508a6d166.jpg", "https://telegra.ph/file/5b8a8879ba305c7530543.jpg", "https://telegra.ph/file/415e5c1b5e06a60fe82d6.jpg", "https://telegra.ph/file/436ad5bc09c983893c330.jpg", "https://telegra.ph/file/866da383c8d2d01177066.jpg", "https://telegra.ph/file/6df8a0ada9eaf1e8e8cb8.jpg", "https:// telegra.ph/file/1f8125bef5d4ee1deeb90.jpg", "https://telegra.ph/file/f4253b875d058d2bf81a5.jpg", "https://telegra.ph/file/c8845eb73e0ee14967d3c.jpg", "https://telegra.ph/file/2fd9d3c1d73f0dd2bbae3.jpg", "https://telegra.ph/file/af862da50380ae37d7a2a.jpg", "https://telegra.ph/file/41bf552a93ed6977a3a04.jpg", "https://telegra.ph/file/ada594c1bd49ad155b5fe.jpg", "https://telegra.ph/file/3ec4974b34cebe7885ae4.jpg", "https://telegra.ph/file/4efeefa467f871646aa29.jpg", "https://telegra.ph/file/c284f7881bfd336642915.jpg", "https://telegra.ph/file/bd3273f5e8d1069dd842c.jpg", "https://telegra.ph/file/b6b464ae72bc07ca9268a.jpg", "https://telegra.ph/file/ee8981a3d4307e7e00ab9.jpg", "https://telegra.ph/file/1b16d00db6229aaf70f19.jpg", "https://telegra.ph/file/749046e4c47bd07b0f006.jpg", "https://telegra.ph/file/18170252e7f2dbf3acbf8.jpg", "https://telegra.ph/file/8e55bb36bf4cd2f4f3a06.jpg", "https://telegra.ph/file/a6a6abf8503e3bdd95cf0.jpg", "https://telegra.ph/file/7c4d5b94f5f3db8204200.jpg", "https://telegra.ph/file/bd2e07c550e78f9488bf5.jpg", "https://telegra.ph/file/de3b6c10bbcc148c380c0.jpg", "https://telegra.ph/file/32660ad9582aa5196ba20.jpg", "https://telegra.ph/file/e9465ec2465bf40591f86.jpg", "https://telegra.ph/file/7c51ba04262804d77fea9.jpg", "https://telegra.ph/file/829964dbc7df2d0d828b6.jpg", "https://telegra.ph/file/1a1d657824563e45c915f.jpg", "https://telegra.ph/file/919b37007c4cc8357ccc3.jpg", "https://telegra.ph/file/a30de31fa02394bc37a2a.jpg", "https://telegra.ph/file/ec854ad32b6ae7fc1e6b8.jpg", "https://telegra.ph/file/217e4b58e4defa8ceb537.jpg", "https://telegra.ph/file/fdac12dd09211aacc0b56.jpg", "https://telegra.ph/file/9d035ce100b9eb5b46ecf.jpg", "https://telegra.ph/file/36c0e534db776052c6c8f.jpg", "https://telegra.ph/file/1e8457bc5b1cbfd4158c5.jpg", "https://telegra.ph/file/70e2d556b309e662f85f6.jpg", "https://telegra.ph/file/5bdc6ae54226bc866aa34.jpg", "https://telegra.ph/file/ac77844e0de1fd34b0f1e.jpg", "https://telegra.ph/file/4e943c7ff6571e44b1cab.jpg", "https://telegra.ph/file/5babe677bcd972c1cd509.jpg", "https://telegra.ph/file/28eed4b2964f5b1805164.jpg", "https://telegra.ph/file/a22d6014c4355a3d49f28.jpg", "https://telegra.ph/file/25ca9e74bf7cb1e76f6c0.jpg", "https://telegra.ph/file/511b7dd8b49971c74270d.jpg", "https://telegra.ph/file/bb3dc24f16839653397b9.jpg", "https://telegra.ph/file/ede7f97c1c8b1a6255929.jpg", "https://telegra.ph/file/55504010908da2a1c40f7.jpg"]

# ________________________________________________________________________________#
# Get it from my.telegram.org
API_ID = int(getenv("API_ID", "12380656"))
API_HASH = getenv("API_HASH", "d927c13beaaf5110f25c505b7c071273")

# ________________________________________________________________________________#
## Get it from @Botfather in Telegram.
BOT_TOKEN = getenv("BOT_TOKEN", "")

# ________________________________________________________________________________#



# ________________________________________________________________________________#


# ________________________________________________________________________________#
# Database to save your chats and stats... Get MongoDB:-  https://telegra.ph/How-To-get-Mongodb-URI-04-06
MONGO_DB_URI = getenv("MONGO_DB_URI", "mongodb+srv://bikash:bikash@bikash.3jkvhp7.mongodb.net/?retryWrites=true&w=majority")


# ________________________________________________________________________________#
# Custom max audio(music) duration for voice chat. set DURATION_LIMIT in variables with your own time(mins), Default to 60 mins.
DURATION_LIMIT_MIN = int(
    getenv("DURATION_LIMIT", "50000")
)  # Remember to give value in Minutes


# ________________________________________________________________________________#
# Duration Limit for downloading Songs in MP3 or MP4 format from bot
SONG_DOWNLOAD_DURATION = int(
    getenv("SONG_DOWNLOAD_DURATION_LIMIT", "500")
)  # Remember to give value in Minutes


# ________________________________________________________________________________#
# You'll need a Private Group ID for this.
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", "-1002983844577"))

SONG_DOWNLOAD_DURATION_LIMIT = int(
    getenv("SONG_DOWNLOAD_DURATION_LIMIT", "500")
)  # Remember to give value in Minutes
# ________________________________________________________________________________#
# A name for your Music bot.
MUSIC_BOT_NAME = getenv("MUSIC_BOT_NAME", "shivani music")
# ________________________________________________________________________________#


# Set it true for abody can't copy and forward bot messages
# ________________________________________________________________________________#
# Your User ID.
OWNER_ID = list(
    map(int, getenv("OWNER_ID", "7792739542").split())
)  # Input type must be interger


# ________________________________________________________________________________#
# Get it from http://dashboard.heroku.com/account
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# You have to Enter the app name which you gave to identify your  Music Bot in Heroku.
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")


# ________________________________________________________________________________#
# For customized or modified Repository
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/masoombalak88/Testing",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")

# GIT TOKEN ( if your edited repo is private)
GIT_TOKEN = getenv(
    "GIT_TOKEN",
    "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",
)


# ________________________________________________________________________________#
# Only  Links formats are  accepted for this Var value.
SUPPORT_CHANNEL = getenv(
    "SUPPORT_CHANNEL", "https://t.me/itz_Cute_Shivani"
)  # Example:- https://t.me/Quizess_prince
SUPPORT_GROUP = getenv(
    "SUPPORT_GROUP", "https://t.me/itz_Cute_Shivani"
)  # Example:- https://t.me/Quizess_prince

# ________________________________________________________________________________#
# Set it in True if you want to leave your assistant after a certain amount of time. [Set time via AUTO_LEAVE_ASSISTANT_TIME]
AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", False)

# Time after which you're assistant account will leave chats automatically.
AUTO_LEAVE_ASSISTANT_TIME = int(
    getenv("ASSISTANT_LEAVE_TIME", "50000")
)  # Remember to give value in Seconds


# ________________________________________________________________________________#
# Time after which bot will suggest random chats about bot commands.
AUTO_SUGGESTION_TIME = int(
    getenv("AUTO_SUGGESTION_TIME", "3000")
)  # Remember to give value in Seconds


# Set it True if you want to bot to suggest about bot commands to random chats of your bots.
AUTO_SUGGESTION_MODE = getenv("AUTO_SUGGESTION_MODE", False)


# ________________________________________________________________________________#
# Set it true if you want your bot to be private only [You'll need to allow CHAT_ID via /authorize command then only your bot will play music in that chat.]
PRIVATE_BOT_MODE = getenv("PRIVATE_BOT_MODE", "False")


# ________________________________________________________________________________## Time sleep duration For Youtube Downloader
YOUTUBE_DOWNLOAD_EDIT_SLEEP = int(getenv("YOUTUBE_EDIT_SLEEP", "3"))

# Time sleep duration For Telegram Downloader
TELEGRAM_DOWNLOAD_EDIT_SLEEP = int(getenv("TELEGRAM_EDIT_SLEEP", "5"))


# ________________________________________________________________________________## Your Github Repo.. Will be shown on /start Command
GITHUB_REPO = getenv(
    "GITHUB_REPO",
)

# ________________________________________________________________________________#
# Spotify Client.. Get it from https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "19609edb1b9f4ed7be0c8c1342039362")
SPOTIFY_CLIENT_SECRET = getenv(
    "SPOTIFY_CLIENT_SECRET", "409e31d3ddd64af08cfcc3b0f064fcbe"
)


# ________________________________________________________________________________#
# Maximum number of video calls allowed on bot. You can later set it via /set_video_limit on telegram
VIDEO_STREAM_LIMIT = int(getenv("VIDEO_STREAM_LIMIT", "5"))


# ________________________________________________________________________________#
# Maximum Limit Allowed for users to save playlists on bot's server
SERVER_PLAYLIST_LIMIT = int(getenv("SERVER_PLAYLIST_LIMIT", "50"))

# MaximuM limit for fetching playlist's track from youtube, spotify, apple links.
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "50"))


# ________________________________________________________________________________#
# Cleanmode time after which bot will delete its old messages from chats
CLEANMODE_DELETE_MINS = int(
    getenv("CLEANMODE_MINS", "5")
)  # Remember to give value in Seconds


# ________________________________________________________________________________#

# Telegram audio  and video file size limit

TG_AUDIO_FILESIZE_LIMIT = int(
    getenv("TG_AUDIO_FILESIZE_LIMIT", "2147483648")
)  # Remember to give value in bytes

TG_VIDEO_FILESIZE_LIMIT = int(
    getenv("TG_VIDEO_FILESIZE_LIMIT", "2147483648")
)  # Remember to give value in bytes

# Chceckout https://www.gbmb.org/mb-to-bytes  for converting mb to bytes


# ________________________________________________________________________________#
# If you want your bot to setup the commands automatically in the bot's menu set it to true.
# Refer to https://i.postimg.cc/Bbg3LQTG/image.png
SET_CMDS = getenv("SET_CMDS", "False")


# ________________________________________________________________________________#
# You'll need a Pyrogram String Session for these vars. Generate String from our session generator bot @YukkiStringBot
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)



BANNED_USERS = filters.user()
YTDOWNLOADER = 1
LOG = 2
LOG_FILE_NAME = "Yukkilogs.txt"
adminlist = {}
lyrical = {}
chatstats = {}
userstats = {}
clean = {}

autoclean = []


# Images





START_IMG_URL = random.choice(XYZ)
PING_IMG_URL = random.choice(XYZ)
PLAYLIST_IMG_URL = random.choice(XYZ)
GLOBAL_IMG_URL = random.choice(XYZ)

STATS_IMG_URL = random.choice(XYZ)

TELEGRAM_AUDIO_URL = random.choice(XYZ)

TELEGRAM_VIDEO_URL = random.choice(XYZ)

STREAM_IMG_URL = random.choice(XYZ)

SOUNCLOUD_IMG_URL = random.choice(XYZ)

YOUTUBE_IMG_URL = random.choice(XYZ)
SPOTIFY_ARTIST_IMG_URL = random.choice(XYZ)

SPOTIFY_ALBUM_IMG_URL = random.choice(XYZ)

SPOTIFY_PLAYLIST_IMG_URL = random.choice(XYZ)

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))
