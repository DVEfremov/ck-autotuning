#
# Collective Knowledge (deal with choices)
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
# Make next multi-dimensional choice (with state)

def make(i):
    """
    Input:  {
              choices_desc       - dict with description of choices (flat format)
              choices_order      - list of list of flat choice vectors to tune [[],[],...] - 
                                   list of list is needed to be able to enable indedepent 
                                   selection of groups of choices. For example, iterate
                                   over all possible data set sizes + random flags per data set
              choices_selection  - list of dicts with types of selection for each above group
              choices_current    - current vector of choices
              (random_module)    - if !=None, random module with seed
              (pipeline)         - if set, update it with current choices
              (custom_explore)   - enforce exploration params from command line

              (all)              - if 'yes', select all
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              choices_current    - list of updated choices
              choices            - dictionary of flat choices and values
              choices_order      - list of flat choices (to know order if need such as for LLVM opt)
              pipeline           - upated pipeline with choices
                                   also choices and choices_order are added to pipeline
              finish             - if True, iterations are over
            }

    """

    from random import Random

    o=i.get('out','')

    my_random=i.get('random_module',None)
    if my_random==None: my_random=Random()

    finish=False

    cdesc=i['choices_desc']
    corder=i['choices_order']
    csel=i['choices_selection']
    ccur=i['choices_current']

    pipeline=i.get('pipeline',{})
    cexp=i.get('custom_explore',{})

    cd=len(corder)

    al=i.get('all','')

    # Init current choices
    if len(ccur)==0:
       for c in range(0, cd):
           cx=corder[c]
           cy=[]
           for k in range(0,len(cx)):
               cy.append('')
           ccur.append(cy)

    update=False
    nupdate=False # if force update next

    for cx in range(cd-1,-1,-1):
        cc=corder[cx]
        dc=ccur[cx]

        t={}
        if al=='yes': 
           tp='pre-selected'
        elif cexp.get('type','')!='':
           tp=cexp['type']
        else:
           t=csel[cx]
           tp=t.get('type','')

        ti=t.get('iterations','')
        top=t.get('omit_probability','')
        if cexp.get('omit_probability','')!='': zestart=cexp['omit_probability']
        if top=='': top=0.0
        else: top=float(top)

        # Take descriptions first directly from choices_selection.
        # Later will be taken from choice_desc, if exists
        zchoice=t.get('choice',[])
        zprefix=t.get('explore_prefix','')
        zdefault=t.get('default','')
        zcanomit=t.get('can_omit','')

        zestart=t.get('start','')
        if cexp.get('start','')!='': zestart=cexp['start']

        zestop=t.get('stop','')
        if cexp.get('stop','')!='': zestop=cexp['stop']

        zestep=t.get('step','')
        if cexp.get('step','')!='': zestep=cexp['step']

        if tp=='': tp='random'

        ci=t.get('cur_iter','')
        if ci=='': ci=-1

        if cx==(cd-1) or update or nupdate or ci==-1:
           nupdate=False

           ci+=1

           if ti!='' and ci>=ti:
              ci=0
              update=True
           else:
              update=False

           dvsame=''
           xupdate=False
           for c in range(len(cc)-1,-1,-1):
               cn=cc[c]

               qt=cdesc.get(cn,{})

               if zcanomit!='': yco=zcanomit
               else: yco=qt.get('can_omit','')

               if len(zchoice)>0: yhc=zchoice
               else:
                  yhc=qt.get('choice',[])
                  if len(yhc)==0:
                     yhc=qt.get('choices',[])

               if zprefix!='': yep=zprefix
               else: yep=qt.get('explore_prefix','')

               if tp!='': ytp=t.get('subtype','')
               else: ytp=qt.get('type','')

               if zdefault!='': ydefault=zdefault
               else: ydefault=qt.get('default','')

               dcc=dc[c]
               if yep!='' and dcc.startswith(yep):
                  dcc=dcc[len(yep):]
                  if ytp=='float': dcc=float(dcc)
                  else: dcc=int(dcc)

               if zestart!='': yestart=zestart
               else: yestart=qt.get('explore_start','')
               if zestop!='': yestop=zestop
               else: yestop=qt.get('explore_stop','')
               if zestep!='': yestep=zestep
               else: yestep=qt.get('explore_step','')

               if yestart!='':
                  if ytp=='float':
                     r1=float(yestart)
                     r2=float(yestop)
                     rs=float(yestep)
                  else:
                     r1=int(yestart)
                     r2=int(yestop)
                     rs=int(yestep)

                  rx=(r2-r1+1)/rs

               dv=ydefault

               # If exploration, set first
#               if tp=='parallel-loop' or tp=='loop':
               if yestart!='': 
                  dv=r1
               elif len(yhc)>0:
                    dv=yhc[0]

               if tp=='pre-selected': 
                  dv=dcc
               elif ci!=0 or (tp=='random' or tp=='random-with-next'):
                  lcqx=len(yhc)
                  if tp=='random' or tp=='random-with-next':
                     omit=False
                     if yco=='yes':
                        x=my_random.randrange(0, 1000)
                        if x<(1000.0*top):
                           omit=True

                     if omit:
                        dv=''
                     else:
                        if lcqx>0:
                           ln=my_random.randrange(0, lcqx)
                           dv=yhc[ln]
                        elif yestart!='':
                             if (type(rx)==float or type(rx)==int or type(rx)==ck.type_long) and rx>=1:
                                y=my_random.randrange(0,int(rx))
                             else:
                                # alternatively should print inconsistency
                                y=0
                             dv=r1+(y*rs)

                     if tp=='random-with-next':
                        nupdate=True

                  elif tp=='parallel-random': # Change all dimensions at the same time (if explorable)!
                       lcqx=len(yhc)
                       if dvsame=='':
                          if lcqx>0:
                             ln=my_random.randrange(0, lcqx)
                             dvsame=yhc[ln]
                          elif yestart!='':
                               if (type(rx)==float or type(rx)==int or type(rx)==ck.type_long) and rx>=1:
                                  y=my_random.randrange(0,int(rx))
                               else:
                                  # alternatively should print inconsistency
                                  y=0
                               dvsame=r1+(y*rs)
                       dv=dvsame

                  elif tp=='parallel-loop' or tp=='loop':
                       dv=dcc
                       if tp=='parallel-loop' or c==len(cc)-1 or xupdate:
                          if yestart!='':
                             dv=dcc+rs
                             if dv>r2:
                                dv=r1
                                if tp=='loop': xupdate=True
                                else: 
                                   ci=0
                                   update=True
                             else:
                                xupdate=False
                          else: # normally choice
                             if dv=='':
                                ln=0
                             else:
                                if dv in yhc:
                                   ln=yhc.index(dv)
                                   ln+=1
                                else:
                                   ln=0
                             if ln<lcqx:
                                dv=yhc[ln]
                                xupdate=False
                             else:
# Next is wrong, but check compatibility with previous cases!
#                                dv=ydefault
                                dv=yhc[0]
                                if tp=='loop': xupdate=True
                                else:
                                   ci=0
                                   update=True

                  # Machine learning based probabilistic adaptive sampling of multi-dimensional 
                  # design and optimization speaces via external plugin
                  # See our work on Collective Mind (2014/2015)
                  #
                  # NOTE: moved to external customized autotuner plugins (see autotune pipeline --custom_autotuner)
#                  elif tp=='machine-learning-based' or tp=='model-based' or tp=='adaptive' or tp=='plugin-based' or tp=='customized': 

                  else:
                     return {'return':1, 'error':'unknown autotuning type ('+tp+')'}

               if yep!='' and dv!='': dv=yep+str(dv)
               dc[c]=dv

           if xupdate:
              update=True

        t['cur_iter']=ci

    corder1=[]
    ccur1={}

    if update: # means that all loops were updated
       finish=True 
    else:
       if o=='con': 
          ck.out('')
          ck.out('  Vector of flattened and updated choices:')


       ll=0
       prt=[]

       for q in range(0, len(corder)):
           qq=corder[q]
           vq=ccur[q]
           for q1 in range(0, len(qq)):
               qq1=qq[q1]
               vq1=vq[q1]

               corder1.append(qq1)
               ccur1[qq1]=vq1

               if o=='con':
                  if vq1!='':
                     if len(qq1)>ll: ll=len(qq1)
                     prt.append({'k':qq1, 'v':vq1})

               rx=ck.set_by_flat_key({'dict':pipeline, 'key':qq1, 'value':vq1})
               if rx['return']>0: return rx
               pipeline=rx['dict']

           # Flatten choices and values, and add to pipeline
           # Useful if order of choices is important (say opt flags in LLVM)
           # Will be decoded by a given pipeline, if needed 
           pipeline['choices_order']=corder1
#           pipeline['choices']=ccur1   

       if o=='con' and len(prt)>0:
          for q in prt:
              k=q['k']
              v=q['v']

              j=ll-len(k)

              x=' '*j

              ck.out('    '+k+x+' : '+str(v))

    return {'return':0, 'choices_current':ccur, 'choices_order':corder1, 'choices':ccur1, 'pipeline':pipeline, 'finish':finish}

##############################################################################
# select list

def select_list(i):
    """
    Input:  {
              choices      - simple text list of choices
              (skip_enter) - if 'yes', do not select 0 when entering 0
              (desc)       - description for each choices entry
            }

    Output: {
              return  - return code =  0, if successful
                                    >  0, if error
              (error) - error text if return > 0
              choice  - selected text
            }

    """

    se=i.get('skip_enter','')

    lst=i.get('choices',[])
    dsc=i.get('desc',[])

    zz={}
    iz=0
    for iz in range(0, len(lst)):
        z=lst[iz]

        zs=str(iz)
        zz[zs]=z

        if iz<len(dsc):
           zd=dsc[iz]
           if zd!='': 
              z+=' ('+zd+')'

        ck.out(zs+') '+z)

        iz+=1

    ck.out('')
    y='Select item'
    if se!='yes': y+=' (or press Enter for 0)'
    y+=': '

    rx=ck.inp({'text':y})
    x=rx['string'].strip()
    if x=='' and se!='yes': x='0' 

    if x not in zz:
       return {'return':1, 'error':'number is not recognized'}

    dduoa=zz[x]

    return {'return':0, 'choice':dduoa}
