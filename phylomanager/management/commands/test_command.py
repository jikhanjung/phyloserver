from multiprocessing.spawn import prepare
from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner, PhyloAnalog
from django.core.management.base import BaseCommand
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal
import subprocess
from phylomanager.utils import PhyloTreefile
from io import StringIO
from Bio import Phylo
import matplotlib.pyplot as plt

from backports import zoneinfo

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        #self.test_localtime()
        self.test_tree()
        #self.test_tree2()
    def test_tree2(self):
        text = "(c:1,(d:2,e:1.5):5)"
        handle = StringIO(text)
        tree = Phylo.read(handle, "newick")
        print(tree)

        tf=PhyloTreefile()
        tree = tf.parse_tree(text)

        print(tree)

    def test_tree(self):
        filename = 'D:/projects/phyloserver/uploads/phylo_run/admin/Cloudina_20220507_222948/1/CLOUDINA_7GNSA85.nex1.con.tre'
        tf = PhyloTreefile()
        tf.readtree(filename,'Nexus')
        #print(tf.tree_text_hash)
        #tree_text = tf.tree_text_hash['con_50_majrule']
        for k in tf.tree_text_hash.keys():

            handle = StringIO(tf.tree_text_hash[k])
            tree = Phylo.read(handle, "newick")
            #print(tf.taxa_hash)
            for clade in tree.find_clades():
                if clade.name and tf.taxa_hash[clade.name]:
                    #print(clade.name)
                    clade.name = tf.taxa_hash[clade.name]
                    #print(clade.name)
            print(tree)


    def test_localtime(self):
        now = timezone.now()
        local_now = timezone.localtime(now)
        #print(now)
        #print(local_now)

        #now_string = now.strftime("%Y%m%d_%H%M%S")
        #timezone.activate(zoneinfo.ZoneInfo(settings.TIME_ZONE))
        #current_tz = timezone.get_current_timezone()
