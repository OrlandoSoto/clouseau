
import os
import sys
import re
import subprocess

# -----------------------------------------------------------------------------------------------
class Parser:    
    """
    Converts git-grep's stdout to Python dictionary
    """
    
    def __init__( self ):
        pass

    def parse_terms( self, patterns_file, single_term ):
        terms = patterns_file.readlines()
        if( single_term != None ):
            terms = { single_term }
        terms = [term.strip() for term in terms if not term.startswith('#')]
        return terms
      


    def parse( self, terms, repo, **kwargs ):
        """
        For each term in @terms perform a search of the git repo and store search results
        (if any) in an iterable.
        """

        # Main results data structure
        clouseau = {}

        pathspec =  kwargs.get( 'pathspec' )
        before = kwargs.get( 'before' )
        after = kwargs.get( 'after' )
        author = kwargs.get( 'author' )
        github_url = kwargs.get( 'github_url' )
        
        clouseau.update( {'meta' : {'github_url': github_url } } )

        revlist = self.generate_revlist( pathspec, before, after, author )
              
        if (revlist == ''):
            #Need to build a more informative Nothing-found iterable
            return clouseau
        
        clouseau = self.search( terms, revlist, clouseau )
        return clouseau
    
    
    
    def search( self, terms, revlist, clouseau ):
        # Lexemes:
        file_name_heading = re.compile( '^[0-9a-zA-Z]{40}:.+$' )
        function_name = re.compile( '^[0-9]+=' )            
        matched_line = re.compile( '^[0-9]+:' ) 
    
        term = None

        #Queue and thread this
        for term in terms:     
            git_grep_cmd = ['git','grep','-inwa', '--heading', '--no-color', \
                                '--max-depth','-1', '-E', '--break', '--', term]
            cmd = git_grep_cmd + revlist.split()

            git_grep = subprocess.Popen( cmd , stderr=subprocess.PIPE, 
                                         stdout=subprocess.PIPE)

            (out,err) = git_grep.communicate()
        
            clouseau.update( {term: {}}  )

            for line in out.split('\n'):
                # We don't  know how a lot of the data is encoded, so make sure it's utf-8 before 
                # processing
                if line == '':
                    continue
                try:
                    line = unicode( line, 'utf-8' ) 
                except UnicodeDecodeError:
                    line = unicode( line, 'latin-1' ) 
                

                if file_name_heading.match( line ):
                    title = line.split(':', 1)[1]
                    title = line.replace('/','_')
                    title = title.replace('.','_').strip()
                    _src = line.strip().encode('utf-8')
                    _srca = _src.split(':', 1)
                    clouseau[term][title] = {'src' : _srca[1] }
                    clouseau[term][title]['refspec'] =  _srca[0]
                    git_log_cmd = subprocess.Popen( ['git', 'log', _srca[0] , '-1'],\
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE )
                    git_log = git_log_cmd.communicate()[0]
                    clouseau[term][title]['git_log'] = [ x.strip() for x in git_log.split('\n') if x != '' ]
                    #clouseau[term][title] = {'ref' : _srca[0] }
                    clouseau[term][title]['matched_lines'] = []
                    continue

                if function_name.match( line ):
                    function = line.split('=')
                    clouseau[term][title].update( {'function': function} ) 
                    #Node( type='function', value=function, parent=node )
                    clouseau[term][title].update( {'matches': len(function)} )
                    continue

                if matched_line.match( line ):
                    matched = line.split(':' , 1)
                    matched[0] = matched[0].strip()
                    matched[1] = matched[1].strip()
                    clouseau[term][title]['matched_lines'].append( matched )
                    continue
                    #Node( type='matched_line', value=line.split(':',1), parent=node )

        return clouseau
    
    
    
    
    
    def generate_revlist(self, pathspec, before, after, author):
            rev_list = None
            #Default rev list
            git_rev_cmd = ['git', 'rev-list', '--all', '--date-order']

            if ( author != None ):
                git_rev_cmd.append( '--author' )
                git_rev_cmd.append( author )
            if ( before != None ):
                git_rev_cmd.append( '--before' )
                git_rev_cmd.append( before )
    
            if ( after != None):
                git_rev_cmd.append( '--after' )
                git_rev_cmd.append( after )
    
            # ---
            if ( pathspec != None and pathspec.lower() == 'all' ):
                git_revlist = subprocess.Popen( git_rev_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE )
                rev_list = git_revlist.communicate()[0]
            elif (pathspec == None):
                git_revlist = subprocess.Popen( git_rev_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE )
                rev_list = git_revlist.communicate()[0]
            else:
                rev_list = pathspec


            return rev_list
