import re, os

class PhyloMatrix:
    def __init__(self):
        self.taxa_list = []
        self.data_list = []
        self.data_hash = {}
        self.n_taxa = 0
        self.n_chars = 0
        self.command_hash = {}
        self.dataset_name = ''
        self.formatted_data_hash = {}

    def matrix_as_string(self,parens=["(",")"],separator=" "):
        matrix_string = ""
        #print("separator=["+separator+"]")
        for taxon in self.taxa_list:
            #print("taxon:",taxon)
            taxon_string = taxon + " "
            #matrix_string += taxon + " "
            formatted_data = self.formatted_data_hash[taxon]
            #print(formatted_data)
            for char_state in formatted_data:
                #print("char:",char_state)
                if type(char_state) is list:
                    taxon_string += parens[0] + separator.join(char_state) + parens[1]
                    #print("poly:",parens[0] + separator.join(char_state) + parens[1])
                else:
                    taxon_string += char_state
            matrix_string += taxon_string + "\n"
        return matrix_string

    def parse_nexus_data_block(self,line_list):
        in_matrix = False
        for line in line_list:
            matrix_begin = re.match("\s*matrix\s*",line,flags=re.IGNORECASE)
            if matrix_begin:
                self.taxa_list = []
                self.data_list = []
                self.data_hash = {}
                in_matrix = True
            elif in_matrix:
                matrix_match = re.match("(\S+)\s+(.+);*",line)
                if matrix_match:
                    species_name = matrix_match.group(1)
                    data_line = matrix_match.group(2)
                    self.taxa_list.append(species_name)
                    self.data_list.append(data_line)
                    self.data_hash[species_name] = data_line
            else:
                #in data block but not in matrix ==> command/variable
                command_match = re.match("^\s*(\S+)\s+(.*);",line.upper(),flags=re.IGNORECASE)
                if command_match:
                    command = command_match.group(1)
                    variable_string = command_match.group(2)
                    variable_list = re.findall("(\w+)\s*=\s*(\S+)",variable_string)
                    #print(variable_list)
                    self.command_hash[command] = {}
                    for variable in variable_list:
                        self.command_hash[command][variable[0]] = variable[1]
                #pass

            matrix_end = re.match(".*;.*",line)
            if matrix_end:
                in_matrix = False
        ntax = int(self.command_hash['DIMENSIONS']['NTAX'])
        nchar = int(self.command_hash['DIMENSIONS']['NCHAR'])
        self.n_taxa = ntax
        self.n_chars = nchar
        #print("number of taxa", ntax, len(self.taxa_list))
        #print("number of char", nchar)
        self.process_polymorphism()

    def command_as_string(self):
        command_string = ""
        for key1 in self.command_hash.keys():
            variable_list = []
            for key2 in self.command_hash[key1].keys():
                variable_list.append( key2 + "=" + self.command_hash[key1][key2] )
            command_string += key1 + " " + " ".join(variable_list) + ";\n"
        return command_string

    def parse_tnt_file(self,line_list):
        in_header = False
        in_body = True
        for line in line_list:
            # check if first line contains dataset name and taxa/chars count
            xread_match = re.match("xread",line,flags=re.IGNORECASE)
            datasetname_match = re.match("'(.*)'",line)
            count_match = re.match("(\d+)\s+(\d+)",line)
            data_match = re.match("^(\S+)\s+(.+)$",line)
            if xread_match:
                in_header = True
            if datasetname_match:
                self.dataset_name = datasetname_match.group(1)
            if count_match and in_header:
                self.n_chars = count_match.group(1)
                self.n_taxa = count_match.group(2)
            if not count_match and not datasetname_match and data_match:
                in_header = False
                in_body = True
                taxon_name = data_match.group(1)
                data = data_match.group(2)
                self.taxa_list.append(taxon_name)
                self.data_list.append(data)
                self.data_hash[taxon_name] = data

        self.process_polymorphism()

    def parse_phylip_file(self,line_list):
        total_linenum = len(line_list)
        sequential_format = False
        interleaved_format = False
        taxon_data_count = 0
        for line in line_list:
            # check if first line contains dataset name and taxa/chars count
            count_match = re.match("^\s*(\d+)\s+(\d+)\s*$",line)
            data_match = re.match("^(\S+)\s+(.+)\s*$",line)
            interleaved_data_match = re.match("^\s+(.+)\s*$",line)
            if count_match:
                self.n_chars = count_match.group(2)
                self.n_taxa = count_match.group(1)
                if int(total_linenum) > 2 * int(self.n_taxa):
                    print("interleaved format")
                    interleaved_format = True
                else:
                    print("sequential format")
                    sequential_format = True

            if not count_match and data_match:
                taxon_name = data_match.group(1)
                data = data_match.group(2)
                self.taxa_list.append(taxon_name)
                self.data_list.append(data)
                self.data_hash[taxon_name] = data
                taxon_data_count += 1

            if interleaved_data_match:
                pass
                
        self.process_polymorphism()

    def process_polymorphism(self):

        for species in self.taxa_list:
            data = self.data_hash[species]
            array_data = []
            #print(species, data)
            #print(species,len(data),data)
            is_poly = False
            for char in data:
                #print(char,)
                if char in [ '(','{','[']:
                    is_poly = True
                    array_data.append([])
                elif char in [ ')','}',']']:
                    is_poly = False
                else:
                    if is_poly:
                        if char != ' ':
                            array_data[-1].append(char)
                    else:
                        array_data.append(char)

            self.formatted_data_hash[species] = array_data
            print(species, len(array_data),array_data)

            #formatted_data = data.split()
            #print(array_data)
            #if len(data) != nchar:
            #else:

        #print(data_hash)
        #print(self.command_hash)

class PhyloDatafile():
    def __init__(self):
        self.file_text = None
        self.line_list = []
        self.block_list = []
        self.block_hash = {}
        self.file_type = None
        self.phylo_matrix = PhyloMatrix()
        self.dataset_name = ''

    def open(self,a_filepath):
        filepath,filename = os.path.split(a_filepath)
        filename, fileext = os.path.splitext(filename.upper())
        self.dataset_name = filename

        # determine by filetype
        if fileext.upper() in ['.NEX','.NEXUS']:
            self.file_type='Nexus'
        elif fileext.upper() in ['.PHY','.PHYLIP']:
            self.file_type='Phylip'
        print("filetype:", self.file_type, filename, fileext)
        
        #read first line
        file = open(a_filepath,mode='r')
        self.file_text = file.read()
        file.close()

        self.line_list = self.file_text.split('\n')
        if not self.file_type:
            upper_file_text = self.file_text.upper()
            #first_line = self.line_list[0].upper()
            if upper_file_text.find('#NEXUS') > -1:
                self.file_type = 'Nexus'
            elif upper_file_text.find('XREAD') > -1:
                self.file_type = 'TNT'
        #print("File type:", self.file_type)
        
        if self.file_type == 'Nexus':
            print("nexus file")
            self.parse_nexus_file()
            if self.block_hash['DATA']:
                self.phylo_matrix.parse_nexus_data_block(self.block_hash['DATA'])
                self.command_hash = self.phylo_matrix.command_hash
        elif self.file_type == 'Phylip':
            print("phylip file")
            self.phylo_matrix.parse_phylip_file(self.line_list)
        elif self.file_type == 'TNT':
            print("TNT file")
            self.phylo_matrix.parse_tnt_file(self.line_list)
            #self.parse_tnt_File()
        
        if self.phylo_matrix.dataset_name != '':
            self.dataset_name = self.phylo_matrix.dataset_name

    def parse_nexus_file(self,line_list=None):
        if not line_list:
            line_list = self.line_list
        curr_block=None
        in_block = False
        for line in line_list:
            #print(line)
            begin_line = re.match("begin\s+(\S+);",line,flags=re.IGNORECASE)
            end_line = re.match("end\s*;",line,flags=re.IGNORECASE)

            if begin_line:
                #print(begin_line)
                curr_block = {}
                curr_block['name'] = begin_line.group(1).upper()
                curr_block['text'] = []
                in_block = True
            elif end_line:
                #print("end block")
                self.block_list.append(curr_block)
                #if curr_block['name'] == 'DATA':
                self.block_hash[curr_block['name']] = curr_block['text']
                in_block = False
            elif in_block:
                curr_block['text'].append(line)
        return #block_list
    
    def matrix_as_string(self):
        return self.phylo_matrix.matrix_as_string()

    def command_as_string(self):
        return self.phylo_matrix.command_as_string()

    def as_phylip_format(self):
        phylip_string = ""
        data_string = self.matrix_as_string()
        phylip_string += str(self.phylo_matrix.n_taxa) + " " + str(self.phylo_matrix.n_chars) + "\n"
        phylip_string += data_string
        return phylip_string

    def as_tnt_format(self):
        tnt_string = ""
        data_string = self.matrix_as_string()
        tnt_string += "xread '" + self.dataset_name + "' " + str(self.phylo_matrix.n_chars) + " " + str(self.phylo_matrix.n_taxa) + "\n"
        tnt_string += data_string
        tnt_string += ";\n"
        return tnt_string

    def as_nexus_format(self):
        nexus_string = ""
        data_string = self.matrix_as_string()
        command_string = self.command_as_string()
        nexus_string += "#NEXUS\n\n"
        nexus_string += "BEGIN DATA;\n"
        nexus_string += command_string
        nexus_string += data_string
        nexus_string += ";\n"
        nexus_string += "END;\n"
        return nexus_string

# Open a file: file
phylo1 = PhyloDatafile()
phylo1.open('scripts/Cloudina_210914_RSOS2.nex')
print(phylo1.as_phylip_format())
print(phylo1.as_nexus_format())
print(phylo1.as_tnt_format())

#phylo2 = PhyloDatafile()
#phylo2.open('scripts/Cloudina_210914_RSOS2.phy')
#print(phylo2.as_phylip_format())

#phylo3 = PhyloDatafile()
#phylo3.open('scripts/20190806_Nisusiid_Matrix.tnt')
#print(phylo3.as_phylip_format())

#print(" ".join(['1','2']))