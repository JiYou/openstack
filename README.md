OpenStack
=========

《OpenStack开源云王者归来》一书所附代码及资料。本书采用OpenStack Grizzly版本。

# 操作系统

操作系统使用ubuntu-12.10-server-amd64.iso。
由于Ubuntu系统各个版本依赖包之间变动较大，请务必使用12.10版本。

有不少读者反应在使用系统时，可能会遇到源的问题，在安装好Ubuntu-12.10之后，可以使用如下网络源（请保证你的系统可以连接至网络）：

deb http://old-releases.ubuntu.com/ubuntu/ quantal main restricted
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal main restricted
deb http://old-releases.ubuntu.com/ubuntu/ quantal-updates main restricted
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal-updates main restricted
deb http://old-releases.ubuntu.com/ubuntu/ quantal universe
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal universe
deb http://old-releases.ubuntu.com/ubuntu/ quantal-updates universe
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal-updates universe
deb http://old-releases.ubuntu.com/ubuntu/ quantal multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal multiverse
deb http://old-releases.ubuntu.com/ubuntu/ quantal-updates multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal-updates multiverse
deb http://old-releases.ubuntu.com/ubuntu/ quantal-backports main restricted universe multiverse
deb-src http://old-releases.ubuntu.com/ubuntu/ quantal-backports main restricted universe multiverse

将/etc/apt/sources.list文件原有内容清空，再复制此内容至/etc/apt/sources.list文件。然后再运行：

    apt-get update

更新源即可。

# 读书必看

    - [读书指南](http://pan.baidu.com/s/1gdzixz1)。在读书时，请务必阅读《第X章 阅读指南》PPT。
    - [实验指南](http://pan.baidu.com/s/1gdzixz1)。在实验时，请务必阅读《第X讲 安装XX》PPT。请从第一讲开始。

# 联系方式
有任何问题，请联系作者 jumail@qq.com
为了更加方便交流，关收OpenStack书籍的任何问题，可加入QQ群345596547即OpenStack品书会。

# 常见问题

由于能力有限，亦加时过境迁，编写的内容总会出现各种错误，请注意关注[常见问题](https://github.com/JiYou/openstack/blob/master/qa.md)。

## 所有资源
本书用到的所有资源都可以从百度云中下载：http://pan.baidu.com/s/1gdzixz1 。
