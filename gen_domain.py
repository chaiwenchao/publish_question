# encoding: utf-8
# python 2
from collections import defaultdict
from argparse import ArgumentParser
import os, sys
import copy
import yaml
import subprocess
from fnmatch import fnmatchcase
import logging

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(levelname)s:%(asctime)s:%(message)s')

usage = '''
Usage:
    python get_domain.py -c cluster_alias -d cluster_domain -conf hadoop_deploy.yaml -i ip_range -dry switchon/off }

    hadoop_deploy.yaml 文件在私有云web1:/home/sys_init/setup/hadoop_deploy_centos/conf/hadoop_deploy.yaml"
    '''


def Usage():
    print(usage)
    sys.exit(-1)


def ExecShellCmd(cmd):
    proc = subprocess.Popen(cmd, shell=True, stderr=None, stdout=subprocess.PIPE)
    for line in proc.stdout:
        print
        line.strip()
    proc.wait()
    if proc.returncode != 0:
        print('Failed to exec shell [%s]' % cmd)
        sys.exit(1)


def send_nginx_conf(cluster, ip, file_lst=None):
    if file_lst is None:
        file_lst = []

    file_lst = [name for name in os.listdir('.') if fnmatchcase(name, '{0}_*'.format(cluster))]
    if len(file_lst) < 12:
        raise Exception('lack of domain file')
    cmd = "scp -r {cluster}_* {ip}:/home/work/nginx/conf/private_cloud/".format(cluster=cluster, ip=ip)
    if cmd:
        ExecShellCmd(cmd)
        logging.info('nginx conf remote copy has been sucess')
        return 'sucess'


def nginx_check(ip):
    cmd = 'ssh {ip} "/home/work/nginx/sbin/nginx {cmdline}"'
    if cmd:
        cmd_new = cmd.format(ip=ip, cmdline='-t')
        ExecShellCmd(cmd_new)
        logging.info('nginx syntax check ok')


def nginx_reload(ip):
    cmd = 'ssh {ip} "/home/work/nginx/sbin/nginx {cmdline}"'
    if cmd:
        cmd_new = cmd.format(ip=ip, cmdline='-s reload')
        ExecShellCmd(cmd_new)


domain_lists = ['marathon', 'mr', 'namenode1', 'namenode2', 'nova', 'rm1', 'rm2', 'spark', 'zabbix', 'test', 'hue',
                'azkaban']
suffix = '.yiducloud.cn'

temp1 = '''
upstream {upstream} {{
    server {host};
}}

server {{
        listen 80;
        server_name {server_name};
#        access_log logs/access_nova.zxyy.yiducloud.cn.log  main;
        location / {{
            proxy_pass http://{upstream};
        }} }}
'''

temp2 = '''
server {{
        listen 80;
        server_name {server_name};
#        access_log logs/access_nova.fyyy.yiducloud.cn.log  main;
        location / {{
            proxy_pass http://{host};
        }}
    }}
'''

temp3 = '''
upstream {upstream} {{
    server {host};
}}

server {{
        listen 80;
        server_name {server_name};
#        access_log logs/access_nova.zxyy.yiducloud.cn.log  main;
        ssl on;
        ssl_certificate /home/work/nginx/conf/ssl/yiducloud-combine.crt;
        ssl_certificate_key /home/work/nginx/conf/ssl/yiducloud.key;
        ssl_dhparam /home/work/nginx/conf/ssl/dhparam.pem;
        location / {{
            proxy_pass http://{upstream};
        }}
    }}
'''


def get_baseinfo(d, h, p, cluster, domain_name):
    upstream = d + '_' + cluster
    host = h + '.' + domain_name + suffix + ':' + p
    server_name = d + '.' + cluster + suffix

    return upstream, host, server_name


def get_domain(cluster, ip, domain_name):
    base_info = defaultdict(dict)
    upstream = ''
    host = ''
    server_name = ''

    for domain in domain_lists:
        if domain == 'namenode1':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop1', '50070', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'namenode2':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop2', '50070', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'rm1':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop1', '8088', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'rm2':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop2', '8088', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'spark':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop1', '18080', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'hue':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop1', '8081', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'mr':
            upstream, host, server_name = get_baseinfo(domain, 'hadoop1', '19888', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = host
            base_info[domain]['server_name'] = server_name

        elif domain == 'azkaban':
            upstream, _, server_name = get_baseinfo(domain, az_host, '8443', cluster, domain_name)

            base_info[domain]['upstream'] = upstream
            base_info[domain]['host'] = az_host + ':8443'
            base_info[domain]['server_name'] = server_name

        elif domain == 'zabbix':
            server_name = domain + '.' + cluster + suffix
            host = '172.18.{ip}.1:8000'.format(ip=ip)
            base_info[domain]['server_name'] = server_name
            base_info[domain]['host'] = host

        elif domain == 'test':
            server_name = domain + '.' + cluster + suffix
            host = '172.18.{ip}.60:8888'.format(ip=ip)
            base_info[domain]['server_name'] = server_name
            base_info[domain]['host'] = host
        else:
            if domain in ['nova', 'marathon']:
                server_name = domain + '.' + cluster + suffix
                host = '172.18.{ip}.60'.format(ip=ip)
                base_info[domain]['server_name'] = server_name
                base_info[domain]['host'] = host
            else:
                logging.info("%s not implement" % domain)

    return base_info


def gen_files(infos, temp, cluster):
    for key in infos:
        file_name = cluster + '_' + key + '.conf'
        with open(file_name, 'w+') as fd:
            temp1 = temp.format(infos[key])
            fd.write(temp1)


def get_azkaban(confMap):
    for kit in confMap['component']:
        for k1 in kit['module']:
            if (k1['name'] == 'offline_client'):
                offline_client = ",".join(k1['hosts'])
                host = offline_client.split(",")[0]
                return host


class DNS:
    def __init__(self, txt, ip):
        if os.path.isfile(txt) and os.stat(txt).st_size > 0:
            with open(txt, 'w+') as fd:
                self._file = txt
        self._file = txt
        self.ip = ip

    def gen(self, baseinfo):
        get_txt = ""
        for key in baseinfo.values():
            server_name_list = key['server_name'].split('.')
            server_name = '.'.join(server_name_list[0:2])
            cmdline = "/home/work/bind/bin/add_dns.sh -t CNAME -u add -n {server_name} -v  ssl-intra-nginx2.qc.yiducloud.cn \n".format(
                server_name=server_name)
            get_txt += cmdline

        with open(self._file, 'a+') as fd:
            fd.write(get_txt)

    def scp(self):
        cmd = "scp {file} {ip}:/tmp/".format(file=self._file, ip=self.ip)
        if cmd:
            ExecShellCmd(cmd)
            return 'ok'

    def exec_cmd(self):
        # cmd ='ssh {ip} "bash /tmp/{file}"'.format(ip=self.ip,file=self._file)
        if args.dry == '1':
            cmd = 'ssh {ip} "bash /tmp/{file}"'.format(ip=self.ip, file=self._file)
            ExecShellCmd(cmd)
            logging.info('Add dns sucess')
        else:
            cmd = 'ssh {ip} "cat /tmp/{file}"'.format(ip=self.ip, file=self._file)
            ExecShellCmd(cmd)


def getArguments():
    """
     Get arguments
    """
    parser = ArgumentParser()
    parser.add_argument('-c', dest='cluster', help='give cluster name')
    parser.add_argument('-i', dest='host', help='ip range info')
    parser.add_argument('-dry', dest='dry', help='The switch on/off')
    parser.add_argument('-d', dest='domain', help='The cloud domain')
    parser.add_argument('-conf', dest='conf', help='The hadoop yaml')

    return parser.parse_args()


if __name__ == '__main__':
    args = getArguments()
    cluster = args.cluster
    ip = args.host
    domain = args.domain
    nginx_ip = '10.10.2.21'
    logging.info('nginx proxy Ip:%s', nginx_ip)

    if not cluster or not ip or not domain or not nginx_ip or not args.conf:
        Usage()
        # raise Exception('lack of parameter')
        logging.info('lack of parameter')

    with open(args.conf, 'r') as fd:
        confMap = yaml.safe_load(fd)
    az_host = get_azkaban(confMap)

    if az_host.find(domain) == int(-1):
        print('hadoop config 文件不匹配')
        sys.exit(-1)

    base_info = get_domain(cluster=cluster, ip=ip, domain_name=domain)
    for key in base_info:
        # raise SystemExit()
        file_name = cluster + '_' + key + '.conf'

        if key in ['azkaban']:
            with open(file_name, 'w+') as fd:
                temp = copy.deepcopy(temp3)
                temp = temp.format(**base_info[key])
                fd.write(temp)

        elif key not in ['marathon', 'nova', 'zabbix', 'test']:

            with open(file_name, 'w+') as fd:
                temp = copy.deepcopy(temp1)
                temp = temp.format(**base_info[key])
                fd.write(temp)

        else:
            with open(file_name, 'w+') as fd:
                temp = copy.deepcopy(temp2)
                temp = temp.format(**base_info[key])
                fd.write(temp)
    logging.info('{} conf generation finshed'.format(cluster))

    # 拷贝conf 远程执行nginx reload
    if args.dry == '1':
        result = send_nginx_conf(cluster, nginx_ip)
        if result == 'sucess':
            nginx_reload(ip=nginx_ip)
    else:
        send_nginx_conf(cluster, nginx_ip)

    logging.info('nginx reload has been finished')
    print('nginx reload has been finished')

    dns = DNS('add_domain.sh', '172.16.124.17')
    dns.gen(base_info)
    ret = dns.scp()
    if ret == 'ok':
        dns.exec_cmd()
    logging.info('All update has been sucess')
    print('All update has been sucess')
