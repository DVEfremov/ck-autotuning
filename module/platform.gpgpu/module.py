#
# Collective Knowledge (platform - GPGPU)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# Detect GPGPU

def detect(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if omitted)
              (os) or (target_os)    - OS module to check (if omitted, analyze host)

              (device_id)            - device id if remote (such as adb)
              (skip_device_init)     - if 'yes', do not initialize device
              (print_device_info)    - if 'yes', print extra device info

              (skip_info_collection) - if 'yes', do not collect info (particularly for remote)

              (skip_print_os_info)   - if 'yes', do not print OS info

              (exchange)             - if 'yes', exchange info with some repo (by default, remote-ck)
              (share)                - the same as 'exchange'
              (exchange_repo)        - which repo to record/update info (remote-ck by default)
              (exchange_subrepo)     - if remote, remote repo UOA
              (exchange_locally)     - if 'yes', exchange locally

              (extra_info)           - extra info about author, etc (see add from CK kernel)

              (type)                 - cuda or opencl
              (quiet)                - select default dependencies
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              features = [
                {
                  gpgpu          - GPGPU features (properties), unified
                  gpgpu_misc     - assorted GPGPU features (properties), platform dependent
                  gpgpu_id       - local ID {'gpgpu_platform_id', 'gpgpu_device_id'}
                }
              ]
            }

    """

    import os

    o=i.get('out','')

    oo=''
    if o=='con': oo=o

    quiet=i.get('quiet','')

    # Various params
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    if tos=='': tos=i.get('os','')
    tdid=i.get('device_id','')

    sic=i.get('skip_info_collection','')
    sdi=i.get('skip_device_init','')
    pdv=i.get('print_device_info','')

    ex=i.get('exchange','')
    if ex=='': ex=i.get('share','')

    einf=i.get('extra_info','')
    if einf=='': einf={}

    # Get OS info
    import copy
    ii=copy.deepcopy(i)
    ii['out']=oo
    if i.get('skip_print_os_info','')=='yes': ii['out']=''
    ii['action']='detect'
    ii['module_uoa']=cfg['module_deps']['platform.cpu']
    rr=ck.access(ii) # DO NOT USE rr further - will be reused as return !
    if rr['return']>0: return rr

    hos=rr['host_os_uid']
    hosx=rr['host_os_uoa']
    hosd=rr['host_os_dict']

    tos=rr['os_uid']
    tosx=rr['os_uoa']
    tosd=rr['os_dict']

    tbits=tosd.get('bits','')

    tdid=rr['device_id']

    # Some params
    ro=tosd.get('redirect_stdout','')
    remote=tosd.get('remote','')
    win=tosd.get('windows_base','')

    stdirs=tosd.get('dir_sep','')

    dv=''
    if tdid!='': dv=' -s '+tdid

    props=[]

    fuid=''
    fuoa=''

    # Check if program to get CUDA device exists
    types=['cuda','opencl']
    tp=i.get('type','')

    if tp=='':
       if i.get('opencl','')=='yes': tp='opencl'
       elif i.get('cuda','')=='yes': tp='cuda'

    if tp!='': types=[tp]

    for tp in types:
        prop={}
        prop_id={}
        prop_all={}
        deps={}

        if o=='con':
           ck.out('************************************************')
           ck.out('Detecting GPGPU type: '+tp)
           ck.out('')

        puoa=cfg['program'][tp]

        r=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['program'],
                     'data_uoa':puoa})
        if r['return']==0:
           # Try to compile program
           r=ck.access({'action':'compile',
                        'module_uoa':cfg['module_deps']['program'],
                        'data_uoa':puoa,
                        'quiet':quiet,
                        'host_os':hos,
                        'target_os':tos,
                        'device_id':tdid,
                        'out':oo})
           if r['return']>0:
              if o=='con':
                 ck.out('Warning: tool compilation failed ('+r['error']+')')
           else:
              # Try to run program
              rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':'.tmp'})
              if rx['return']>0: return rx
              ftmp=rx['file_name']

              r=ck.access({'action':'run',
                           'module_uoa':cfg['module_deps']['program'],
                           'data_uoa':puoa,
                           'extra_run_cmd':'> '+ftmp,
                           'quiet':quiet,
                           'host_os':hos,
                           'target_os':tos,
                           'device_id':tdid,
                           'out':oo})
              if r['return']>0:
                 return r

              deps=r['deps']

              er=i.get('exchange_repo','')
              esr=i.get('exchange_subrepo','')
              el=i.get('exchange_locally','')
              if el!='yes' and er=='': 
                 er=ck.cfg['default_exchange_repo_uoa']
                 esr=ck.cfg['default_exchange_subrepo_uoa']
              xn=prop.get('name','')

              r=ck.load_text_file({'text_file':ftmp, 'split_to_list':'yes', 'delete_after_read':'yes'})
              if r['return']==0:
                 ll=r['lst']

                 for l in ll:
                     if l=='':
                        # Process if features are not empty
                        if len(prop_id)>0:
                           fuoa=''
                           fuid=''

                           # Exchanging info #################################################################
                           if ex=='yes':
                              if o=='con':
                                 ck.out('')
                                 ck.out('Exchanging information with repository ...')

                              ii={'action':'exchange',
                                  'module_uoa':cfg['module_deps']['platform'],
                                  'sub_module_uoa':work['self_module_uid'],
                                  'repo_uoa':er,
                                  'data_name':prop.get('name',''),
                                  'extra_info':einf,
                                  'all':'yes',
                                  'dict':{'features':prop, 'features_misc':prop_all}} 
                              if esr!='': ii['remote_repo_uoa']=esr
                              r=ck.access(ii)
                              if r['return']>0: return r

                              fuoa=r.get('data_uoa','')
                              fuid=r.get('data_uid','')

                              prop=r['dict'].get('features',{})
                              prop_all=r['dict'].get('features_misc',{})

                              if o=='con' and r.get('found','')=='yes':
                                 ck.out('  GPGPU CK entry already exists ('+fuid+') - loading latest meta (features) ...')

                           if tp=='cuda':
                              cc=prop_all.get('gpu compute capability','')

                              cc1=''
                              cc2=''
                              cc3=''

                              if cc=='1.0': 
                                 cc1='compute_10'
                                 cc2='sm_10'
                                 cc3='Tesla'
                              elif cc=='1.1': 
                                 cc1='compute_11'
                                 cc2='sm_11'
                                 cc3='Tesla'
                              elif cc=='1.2': 
                                 cc1='compute_12'
                                 cc2='sm_12'
                                 cc3='Tesla'
                              elif cc=='1.3': 
                                 cc1='compute_13'
                                 cc2='sm_13'
                                 cc3='Tesla'
                              elif cc=='2.0': 
                                 cc1='compute_20'
                                 cc2='sm_20'
                                 cc3='Fermi'
                              elif cc=='2.1': 
                                 cc1='compute_20'
                                 cc2='sm_21'
                                 cc3='Fermi'
                              elif cc=='3.0': 
                                 cc1='compute_30'
                                 cc2='sm_30'
                                 cc3='Kepler'
                              elif cc=='3.2': 
                                 cc1='compute_32'
                                 cc2='sm_32'
                                 cc3='Kepler'
                              elif cc=='3.5': 
                                 cc1='compute_35'
                                 cc2='sm_35'
                                 cc3='Kepler'
                              elif cc=='3.7': 
                                 cc1='compute_37'
                                 cc2='sm_37'
                                 cc3='Kepler'
                              elif cc=='5.0': 
                                 cc1='compute_50'
                                 cc2='sm_50'
                                 cc3='Maxwell'
                              elif cc=='5.2': 
                                 cc1='compute_52'
                                 cc2='sm_52'
                                 cc3='Maxwell'
                              elif cc=='5.3': 
                                 cc1='compute_53'
                                 cc2='sm_53'
                                 cc3='Maxwell'
                              elif cc=='6.0': 
                                 cc1='compute_60'
                                 cc2='sm_60'
                                 cc3='Pascal'
                              elif cc=='6.1': 
                                 cc1='compute_61'
                                 cc2='sm_61'
                                 cc3='Pascal'
                              elif cc=='6.2': 
                                 cc1='compute_62'
                                 cc2='sm_62'
                                 cc3='Pascal'
                              elif cc=='7.0': 
                                 cc1='compute_70'
                                 cc2='sm_70'
                                 cc3='Volta'
                              elif cc=='7.1': 
                                 cc1='compute_71'
                                 cc2='sm_71'
                                 cc3='Volta'
                              else:
                                 return {'return':1, 'error':'Compute capability of your CUDA device is not recognized ('+cc+') - please report to the authors or update module:platform.gpgpu'}

                              prop_all['compute_capability1']=cc1
                              prop_all['compute_capability2']=cc2
                              prop_all['compute_capability3']=cc3

                              prop['microarchitecture']=cc3

                           jj={"gpgpu":prop, "gpgpu_id":prop_id, "gpgpu_misc":prop_all}

                           if fuoa!='' or fuid!='':
                              jj['gpgpu_uoa']=fuoa
                              jj['gpgpu_misc_uid']=fuid

                           # Print without deps if needed
                           if o=='con':
                              ck.out('')
                              ck.out('Features (properties) in JSON:')

                              r=ck.dumps_json({'dict':jj})
                              if r['return']>0: return r
                              s=r['string']

                              ck.out('')
                              ck.out(s)

                           jj['gpgpu_deps']=deps

                           props.append(jj)

                        # Refresh
                        prop={}
                        prop_id={}
                        prop_all={}

                     # Process features
                     lx=[]
                     if l!='':
                        lx=l.split(':')

                     if len(lx)>1:
                        k=lx[0].strip().lower()
                        v=lx[1].strip()

                        if tp=='cuda':
                           if k=='gpu device id':
                              prop_id['gpgpu_device_id']=v
                           elif k=='gpu name':
                              prop['name']=v
                              prop['type']=tp
                           else:
                              prop_all[k]=v
                        else:
                           if k=='platform id':
                              prop_id['gpgpu_platform_id']=v
                           elif k=='device id':
                              prop_id['gpgpu_device_id']=v
                           elif k=='device':
                              prop['name']=v
                              prop['type']=tp
                           elif k=='vendor':
                              prop['vendor']=v
                           else:
                              prop_all[k]=v

    return {'return':0, 'features':{'gpgpu':props}}

##############################################################################
# viewing entries as html

def show(i):
    """
    Input:  {
              data_uoa
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              html         - generated HTML
            }

    """


    h='<h2>GPGPUs (CUDA/OpenCL) participating in crowd-tuning</h2>\n'

    h+='<i>View/update meta information in <a href="http://github.com/ctuning/ck">CK format</a> via <a href="http://github.com/ctuning/ck-crowdtuning-platforms">GitHub</a> ...</i><br><br>\n'

    h+='<table class="ck_table" border="0" cellpadding="6" cellspacing="0">\n'

    # Check host URL prefix and default module/action
    rx=ck.access({'action':'form_url_prefix',
                  'module_uoa':'wfe',
                  'host':i.get('host',''), 
                  'port':i.get('port',''), 
                  'template':i.get('template','')})
    if rx['return']>0: return rx
    url0=rx['url']

    h+=' <tr style="background-color:#cfcfff;">\n'
    h+='  <td><b>\n'
    h+='   #\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   Vendor\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   Name\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   Type\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   <a href="'+url0+'wcid='+work['self_module_uoa']+':">CK UID</a>\n'
    h+='  </b></td>\n'
    h+=' </tr>\n'

    ruoa=i.get('repo_uoa','')
    muoa=work['self_module_uoa']
    duoa=i.get('data_uoa','')

    r=ck.access({'action':'search',
                 'module_uoa':muoa,
                 'data_uoa':duoa,
                 'repo_uoa':ruoa,
                 'add_info':'yes',
                 'add_meta':'yes'})
    if r['return']>0: 
       return {'return':0, 'html':'Error: '+r['error']}

    lst=r['lst']

    num=0
    for q in sorted(lst, key = lambda x: (x.get('meta',{}).get('features',{}).get('vendor','').upper(), \
                                          x.get('meta',{}).get('features',{}).get('name','').upper())):

        num+=1

        duoa=q['data_uoa']
        duid=q['data_uid']

        meta=q['meta']
        ft=meta.get('features',{})
        
        name=ft.get('name','')
        vendor=ft.get('vendor','')
        tp=ft.get('type','')

        h+=' <tr>\n'
        h+='  <td valign="top">\n'
        h+='   '+str(num)+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   '+vendor+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   '+name+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   '+tp+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   <a href="'+url0+'wcid='+work['self_module_uoa']+':'+duid+'">'+duid+'</a>\n'
        h+='  </td>\n'
        h+=' </tr>\n'

    h+='</table><br><br>\n'

    return {'return':0, 'html':h}
