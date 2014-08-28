常见问题
=================================

# 如何下载Github资源？

有以下几种方法：

>* 1. 使用git工具，但务必不要使用Windows上的git tools，Windows git工具会默认自动转码，
   以致拷贝至Linux之后，出现不能解释或者运行的情况。

>* 2. https://github.com/jiyou/openstack 页面右边有Clone Zip按钮，可以点此按钮直接下载，
   再拷贝至Linux机器。

>* 3. Ubuntu节点上，运行`wget https://github.com/JiYou/openstack/archive/master.zip -o openstack.zip`。

>* 4. 也可到百度云上下载http://pan.baidu.com/s/1jG3LX58 ，极力推荐。

# 源的配置

## 方法1

由于ubuntu-12.10官方法极不稳定。为了方便使用，当安装好ubuntu-12.10之后，请照如下步骤配置源：

>* 安装openssh-server: 在利用ubuntu-12.10-server-amd64.iso安装时，请务必勾选openssh-server，如下图：

   ![勾选OpenSSH-server](./vm-install-openssh.png)

>* 下载github资源。

>* 解压下载的安装包。

>* cd ./openstack #就是解压后的目录，如果名字不一样，请更改目录名。

>* ./create_link.sh

>* cd ./chap10/allinone && ./create_http_repo.sh

>* 就可以正确地创建好本地可用的repo。

>* 此外，书中编译源码安装MySQL和源码编译Libvirt的部分可以跳过（实际应用场景比较少）。

## 方法2
>* 下载只含deb包的离线包：http://pan.baidu.com/s/1kTA58Q7 。

>* 解压之后形成如下目录(如果你是放在/opt/目录下解压的，你只需要检查一下就可以了)::

   ![目录树结构](./vm-opt-tree.png)

    当然，实际上你的目录结构和这个并不相符合，你会发现/opt/debs目录下有着更多的deb包。
    如果发现是这样，那么请继续下一步。

>* 修改/etc/apt/sources.list，内容如下(只保留这一行)::

    deb file:///opt/ debs/

>* 运行::

    apt-get update

>* 如果运行成功，则证明建立成功。

>* 查看命令输出，如果有如下输出，则说明成功：


# 配置NTP服务

主节点例如ceph01，ceph02, ceph03。
其中ceph01提供时间服务，其他节点则向ceph01查询时间。


## ceph01时间服务器配置如下：

### Step 1 下载源码并编译

        cd /opt/
        wget http://www.eecis.udel.edu/~ntp/ntp_spool/ntp4/ntp-4.2/ntp-4.2.6p5.tar.gz
        tar zxf ntp-4.2.6p5.tar.gz
        cd ntp-4.2.6p5/
        ./configure --prefix=/usr
        make
        make install

### Step 2 配置

        mkdir -p /etc/ntp
        groupadd ntpd
        mkdir -p /usr/local/ntp
        useradd ntpd -g ntpd -d /usr/local/ntp -s /sbin/nologin
        mkdir -p /var/log/ntp


### Step 3 编写ntp.conf

        file=/etc/ntp.conf
        echo "restrict default kod nomodify notrap nopeer noquery" > $file
        echo "restrict 0.0.0.0 mask 0.0.0.0 kod nomodify notrap nopeer noquery notrust" >> $file
        echo "restrict 127.0.0.1 mask 255.255.0.0 kod" >> $file
        echo "restrict 127.0.0.1" >> $file
        echo "server 127.127.1.0 fudge" >> $file
        echo "127.127.1.0 stratum 8" >> $file
        echo "keys /etc/ntp/keys" >> $file
        echo "trustedkey 1 2 3 4 5 6 7 8 9 10" >> $file

### Step 4 生成ntp认证keys

        olddir=`pwd`
        cd /tmp/
        rm -rf ntpkey*
        ntp-keygen -M
        cat `ls ntpkey* | head -1` | grep MD5  > /etc/ntp/keys
        rm -rf ntpkey*
        cd $olddir

### Step 5 随系统启动

        sed -i "/exit/d" /etc/rc.local
        echo "/usr/bin/ntpd &" >> /etc/rc.local
        echo "exit 0" >> /etc/rc.local


### Step 6 启动ntpd

        ntpd -k /etc/npt/keys


## 子节点配置

所有子节点都需要如下配置

>* 注意ceph01是指向服务器节点，注意根据你的环境进行更改。

### Step 1 下载源码并编译

        cd /opt/
        wget http://www.eecis.udel.edu/~ntp/ntp_spool/ntp4/ntp-4.2/ntp-4.2.6p5.tar.gz
        tar zxf ntp-4.2.6p5.tar.gz
        cd ntp-4.2.6p5/
        ./configure --prefix=/usr
        make
        make install

### Step 2 配置

        mkdir -p /etc/ntp
        groupadd ntpd
        mkdir -p /usr/local/ntp
        useradd ntpd -g ntpd -d /usr/local/ntp -s /sbin/nologin
        mkdir -p /var/log/ntp


### Step 3 编写ntp.conf

        file=/etc/ntp.conf
        echo "restrict default kod nomodify notrap nopeer noquery" > $file
        echo "restrict 0.0.0.0 mask 0.0.0.0 kod nomodify notrap nopeer noquery notrust" >> $file
        echo "restrict 127.0.0.1 mask 255.255.0.0 kod" >> $file
        echo "restrict 127.0.0.1" >> $file
        echo "server 127.127.1.0 fudge" >> $file
        echo "127.127.1.0 stratum 8" >> $file
        echo "keys /etc/ntp/keys" >> $file
        echo "trustedkey 1 2 3 4 5 6 7 8 9 10" >> $file

### Step 4 拷贝keys

        scp -pr ceph01:/etc/ntp/keys /etc/ntp/

### Step 5 编辑contab文件

        echo "10 *    * * *   root    /usr/sbin/ntpdate -a 1 -k /etc/ntp/keys ceph01;hwclock -w" >> /etc/crontab
        ntpdate -a 1 -k /etc/ntp/keys ceph01
        crontab -u root /etc/crontab

如果有看到`28 Aug 11:02:39 ntpdate[25429]: adjust time server 10.239.131.159 offset -0.000301 sec`输出，则说明成功。

>* 如果发现不成功，请注意是否关闭防火墙，`ufw disable`。如果不想关闭防火墙，请查询防火墙关于NTP服务的配置。
