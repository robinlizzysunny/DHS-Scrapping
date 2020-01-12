from bs4 import BeautifulSoup as bs
import networkx as nx
import pandas as pd
import requests
from tqdm import tqdm
import pickle


DHS = nx.Graph()        #Graph Initilization
page = bs(open('dhsContent.html'), 'lxml')


urlbase = 'https://dhsprogram.com/Data/Guide-to-DHS-Statistics/'
with tqdm(total=len(page.find_all('p'))) as pbar:
    for p in page.find_all('p'):
        if p.attrs['class'][0] =='Toc1':
            domain = p.text.replace('\n', '').replace('  ',' ').split(') ')[1]
            domain_href = p.find('a').attrs['href']
            DHS.add_node(domain, type='domain', href=domain_href)
#            print(domain_href)
        elif p.attrs['class'][0] == 'Toc2':
            subdomain = p.text.replace('\n','').replace('  ',' ')
            subdomain_href = p.find('a').attrs['href']
            DHS.add_node(subdomain, type='subdomain', href=subdomain_href)
            DHS.add_edge(subdomain, domain)
            if subdomain == 'Experience of Physical or Sexual Violence by Anyone: Different Combinations':
                subdomain_url = 'https://dhsprogram.com/Data/Guide-to-DHS-Statistics/Persons_Committing_Sexual_Violence.htm?rhtocid=_20_3_0#Among_women_who_have1bc-1'
            else :
                subdomain_url= rf'{urlbase}{subdomain_href}'
            subdomain_webpage = requests.get(subdomain_url).content
            table_list = pd.read_html(subdomain_webpage)
            if subdomain == 'Experience of Physical or Sexual Violence by Anyone: Different Combinations':
                url1 = 'https://dhsprogram.com/Data/Guide-to-DHS-Statistics/Persons_Committing_Sexual_Violence.htm?rhtocid=_20_3_0#Among_women_who_have1bc-1'
                url2 = 'https://dhsprogram.com/Data/Guide-to-DHS-Statistics/Persons_Committing_Physical_Violence.htm?rhtocid=_20_1_0#Among_women_who_havebc-1'
                d1 = pd.read_html(url1)[0]
                d2 = pd.read_html(url2)[0]
                table_d1_d2 = pd.concat([d1,d2], axis=0)
                table_list = [table_d1_d2]
            # addinf exception
            elif subdomain == 'Breastfeeding and Complementary Feeding':
                table_list_ture = [table_list[0], table_list[0], table_list[3], table_list[4], table_list[0]]
                table_list = table_list_ture
            elif subdomain == 'Current Fertility':
                del table_list[2:7]
            elif subdomain == 'Anemia Status':
                del table_list[2]
            elif (subdomain == 'Contraceptive Discontinuation' or subdomain == 'Adult Mortality Rates'):
                table_list = [table_list[0], table_list[-1]]
            #for ij in table_list: print('\n\n', ij)
            subdomain_soup = bs(requests.get(subdomain_url).content, 'lxml')
            try:
                if subdomain == 'Breastfeeding and Complementary Feeding':
                    subdomain_dataset_list_name = ['KR file.','KR file.','KR file.','KR file.','KR file.']
                elif (subdomain == 'Anemia Status' or subdomain == 'Nutritional Status'):
                    subdomain_dataset_list_name = ['PR file.','IR file.','MR file.']
                elif  subdomain == 'Source of Advice or Treatment for Children with Diarrhea':
                    subdomain_dataset_list_name = ['KR file.']
                elif subdomain == 'Hemoglobin <8.0 g/dl in Children':
                    subdomain_dataset_list_name = ['IR file.']
                elif (subdomain == 'Vaccination' or subdomain == 'Prevalence and Treatment of Symptoms of Acute Respiratory Infection (ARI)'):
                    subdomain_dataset_list_name = ['KR file.','KR file.']
                elif subdomain == 'Source of Mosquito Nets':
                    subdomain_dataset_list_name = ['HR file.']
                elif subdomain == 'Use of Intermittent Preventive Treatment (IPTp) by Women during Pregnancy':
                    subdomain_dataset_list_name = ['IR file.']
                elif subdomain == 'Knowledge of HIV Prevention Methods' or subdomain == 'Comprehensive Knowledge about HIV (Total and Youth)':
                    subdomain_dataset_list_name = ['IR file.,MR file.', 'IR file.,MR file.']
                elif subdomain == 'Type of Antimalarial Drugs Used':
                    subdomain_dataset_list_name == ['HR file.,IR file.']
                else:
                    subdomain_dataset_list= subdomain_soup.find_all('span',text=lambda x: x and x.startswith('Vari'))
                    subdomain_dataset_list_name = [ele.next_sibling for ele in subdomain_dataset_list]
                    if  subdomain_dataset_list_name == []:
                        subdomain_dataset_list = subdomain_soup.find_all('span', text=lambda x: x and x.endswith('file.'))
                        subdomain_dataset_list_name = [ele.text for ele in subdomain_dataset_list]
            except Exception as e:
                pass
                #print(subdomain_dataset_list_name)
            subsection_number = 0
#            print('\t', subdomain)
        elif  p.attrs['class'][0] == 'Toc3':
            subsection = p.text.replace('\n','').replace('  ',' ')
            subsection_href = p.find('a').attrs['href']
            DHS.add_node(subsection,type='subsection')
            DHS.add_edge(subsection, subdomain)
            #print(subdomain_dataset_list_name)
            dataset_name =  subdomain_dataset_list_name[subsection_number]
            dataset_name = dataset_name.replace('.','').replace(': ','').replace(' or ',',').replace(' file','').replace(' ','')
            datasets = dataset_name.split(',')
            for dataset in datasets:
                if not dataset in DHS:
                    DHS.add_node(dataset, type='Dataset')
                DHS.add_edge(dataset, subdomain)
            for a,b in table_list[subsection_number].iterrows():
                var = b[0].split(',')[0]
                if not var in DHS:
                    DHS.add_node(var, type='Variable', data_label=b[1])
                DHS.add_edge(var, subdomain)
            subsection_number += 1
#            print('\t\t', subsection)
        pbar.update(1)

list_domain = [n for n, d in DHS.node(data=True) if d['type'] == 'domain' ]
with open('list_domain.pkl','wb') as f: pickle.dump(list_domain, f)
list_subdomain = [n for n, d in DHS.node(data=True) if d['type'] == 'subdomain' ]

list_subdomain.remove('Household Possession of Mosquito Nets')
list_subdomain.remove('Access to an Insecticide-Treated Net (ITN)')
list_subdomain.remove('Use of Mosquito Nets by Persons in the Household')
list_subdomain.remove('Use of Existing ITNs')
list_subdomain.remove('Use of Mosquito Nets by Children')
list_subdomain.remove('Use of Mosquito Nets by Pregnant Women')
list_subdomain.remove('Ever Use of Contraceptive Methods')
list_subdomain.remove('Knowledge of Contraceptive Methods')

with open('list_subdomain.pkl','wb') as f: pickle.dump(list_subdomain,f)
nx.write_gpickle(DHS, "DHS_Graph.gpickle")


print([n for n, d in DHS.node(data=True) if d['type'] == 'Variable' ])

