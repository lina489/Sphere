#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 03/10/2020

@author: Wilfried - IRAP

Software to manipulate projections for the sphere orb.
"""

import matplotlib
matplotlib.use('TkAgg')

import tkinter   as     tk
from   tkinter   import ttk
from   signal    import signal, SIGINT

from   functools import reduce
from   threading import Thread
import os.path   as     opath

# Program imports
import setup
from   sigint    import sigintHandler   
from   tab       import Tab           as     myTab
from   validate  import Validate

class mainApplication:
    '''
    Main application where all the different layouts are defined.
    '''
    
    def __init__(self, parent):
        '''
        Inputs
        ------
            parent : tk.Tk instance
                root propagated throughout the different Frames and Canvas
        '''

        self.parent            = parent
        self.color             = 'white smoke'
        self.parent.config(cursor='arrow')
        
        # Initial program setup
        self.font, self.loadPath, icons, projects, errCode = setup.init()
        
        if errCode != 0:
            print('YAML configuration could not be read correctly. A new one with default values has been created instead.')
       
        
        ######################################################
        #               Check for old projects               #
        ######################################################
        
        # If project file still exists, add it to the list
        self.projects = []
        for proj in projects:
            if opath.isfile(proj):
                self.projects.append(proj)
                
        # It at least one project exist, show validation window at startup
        if len(self.projects) > 0:
            
            # All the names combined into one string
            names  = reduce(lambda a,b: a+b, ['%s, ' %i if pos!=len(self.projects)-1 else str(i) for pos, i in enumerate(self.projects)])
            
            # Validation window
            window = Validate(self, self, parent, 
                              text='You have old projects saved in the setting file. Do you want to open them:%s' %names,
                              splitText=names, title='Open old projects ?',
                              textProperties={'highlightthickness':0, 'bd':0, 'bg':self.color},
                              textFrameProperties={'bg':self.color},
                              buttonsProperties={'bg':'floral white', 'activebackground':'linen'},
                              winProperties={'bg':self.color},
                              acceptFunction=lambda *args, **kwargs: self.loadProjects(self.projects))
            
            self.parent.lift()
            window.grab_set()
            window.geometry('+%d+%d' %( self.parent.winfo_screenwidth()//2 - 5*window.winfo_reqwidth()//4, self.parent.winfo_screenheight()//2 - window.winfo_reqheight()//4))
            window.state('normal')
        
        
        ###########################################################
        #                    Custom ttk styles                    #
        ###########################################################
        
        # Custom style for Notebook
        self.style  = ttk.Style()
        self.style.configure('main.TNotebook', background=self.color)
        
        self.style.configure('main.TNotebook.Tab', padding=[5, 2], font=('fixed', 10))
        self.style.map('main.TNotebook.Tab',
                       background=[("selected", 'lavender'), ('!selected', 'white smoke')],
                       foreground=[('selected', 'RoyalBlue2')])
        
        
        #############################################################
        #               Load icons into Image objects               #
        #############################################################
        self.iconDict               = {}
        self.iconDict['FOLDER']     = tk.BitmapImage(data=icons['FOLDER'],     maskdata=icons['FOLDER_MASK'],     background='goldenrod')
        self.iconDict['FOLDER_256'] = tk.BitmapImage(data=icons['FOLDER_256'], maskdata=icons['FOLDER_256_MASK'], background='goldenrod')
        self.iconDict['DELETE']     = tk.BitmapImage(data=icons['DELETE'],     maskdata=icons['DELETE_MASK'],     background='light cyan', foreground='black')
        
        
        #############################################
        #                 Top frame                 #
        #############################################
        
        # Top frame with buttons and sliders
        self.topframe    = tk.Frame( self.parent, bg=self.color, bd=0, relief=tk.GROOVE)
        
        self.loadButton  = tk.Button(self.topframe, image=self.iconDict['FOLDER'], 
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground='black')
        
        self.delButton   = tk.Button(self.topframe, image=self.iconDict['DELETE'], 
                                     bd=0, bg=self.color, highlightbackground=self.color, relief=tk.FLAT, activebackground=self.color)
        
        self.scaleframe  = tk.Frame( self.topframe, bg=self.color, bd=0, highlightthickness=0)
        
        self.latScale    = tk.Scale( self.scaleframe, length=200, width=12, orient='horizontal', from_=-90, to=90,
                                     cursor='hand1', label='Latitude',
                                     bg=self.color, bd=1, highlightthickness=1, highlightbackground=self.color, troughcolor='lavender', activebackground='black', font=('fixed', 11))
        
        self.longScale   = tk.Scale( self.scaleframe, length=200, width=12, orient='horizontal', from_=-180, to=180,
                                     cursor='hand1', label='Longitude',
                                     bg=self.color, bd=1, highlightthickness=1, highlightbackground=self.color, troughcolor='lavender', activebackground='black', font=('fixed', 11))
        
        
        ###########################################################
        #                     Bottom notebook                     #
        ###########################################################
        
        self.notebook    = ttk.Notebook(self.parent, style='main.TNotebook')
        
        # Keep track of notebook tabs
        self.tabs        = {}
        self.addTab()
        
        
        #######################################################################
        #                               Bindings                              #
        #######################################################################
        
        self.loadButton.bind('<Enter>',    lambda *args, **kwargs: self.tabs[self.notebook.select()].loadButton.configure(bg='black')    if not self.tabs[self.notebook.select()].loaded else None)
        self.loadButton.bind('<Leave>',    lambda *args, **kwargs: self.tabs[self.notebook.select()].loadButton.configure(bg='lavender') if not self.tabs[self.notebook.select()].loaded else None)
        self.loadButton.bind('<Button-1>', lambda *args, **kwargs: self.tabs[self.notebook.select()].load())
        
        
        self.delButton.bind( '<Enter>',    lambda *args, **kwargs: self.iconDict['DELETE'].configure(foreground='red',   background=self.color))
        self.delButton.bind( '<Leave>',    lambda *args, **kwargs: self.iconDict['DELETE'].configure(foreground='black', background='light cyan'))
        self.delButton.bind( '<Button-1>', lambda *args, **kwargs: self.delTab())
        
        self.latScale.bind(  '<Enter>',    lambda *args, **kwargs:self.latScale.configure(highlightbackground='RoyalBlue2'))
        self.latScale.bind(  '<Leave>',    lambda *args, **kwargs:self.latScale.configure(highlightbackground=self.color))
        self.longScale.bind( '<Enter>',    lambda *args, **kwargs:self.longScale.configure(highlightbackground='RoyalBlue2'))
        self.longScale.bind( '<Leave>',    lambda *args, **kwargs:self.longScale.configure(highlightbackground=self.color))
        
        # Drawing frames
        self.loadButton.pack(side=tk.LEFT, pady=10, padx=10)
        self.delButton.pack( side=tk.LEFT, pady=10)
        self.topframe.pack(fill='x')
        
        self.latScale.pack(  side=tk.LEFT,  pady=10, padx=10)
        self.longScale.pack( side=tk.LEFT,  pady=10, padx=10)
        self.scaleframe.pack(side=tk.RIGHT, padx=10, fill='x', expand=True)
        
        self.notebook.pack(fill='both', expand=True)
        
        
    ##########################################################
    #                    Tab interactions                    #
    ##########################################################
    
    def addTab(self, *args, **kwargs):
        '''Add a new tab in the tab list.'''
        
        tab                                 = myTab(self.notebook, self, self.notebook, properties={'bg':'lavender', 'bd':1, 'highlightthickness':0})
        self.tabs[self.notebook.tabs()[-1]] = tab
        return
    
    def delTab(self, *args, **kwargs):
        '''Delete a tab if some conditions are met'''
     
        # Remove the tab from the notebook AND the tab dictionary
        idd = self.notebook.select()
        if self.tabs[idd].loaded:
            self.notebook.forget(idd)
            self.tabs.pop(idd)
        return
    
    def loadProjects(self, files, *args, **kwargs):
        '''
        Load the projects listed in files at startup only.
        
        Parameters
        ----------
            files : list of str
                projects yaml configuration files to load
        '''
        
        for f in files:
            idd = self.notebook.select()
            self.tabs[idd].load(f)
            self.notebook.select(self.notebook.tabs()[-1])
        return
        
    
class runMainloop(Thread):
    '''Class inheriting from threading.Thread. Defined this way to ensure that SIGINT signal from the shell can be caught despite the mainloop.'''
    
    def run(self):
        '''Run method from Thread called when using start()'''
        
        self.root = tk.Tk()
        self.root.title('Sphere - projections at hand')
        self.root.geometry('800x800+%d+%d' %(self.root.winfo_screenwidth()//2-400, self.root.winfo_screenheight()//2-400))
        
        app  = mainApplication(self.root)
        
        self.root.protocol("WM_DELETE_WINDOW", lambda signal=SIGINT, frame=None, obj=self, skipUpdate=True: sigintHandler(signal, obj, None, skipUpdate))
        
        #imgicon = ImageTk.PhotoImage(PROGRAMICON)
        #self.root.tk.call('wm', 'iconphoto', self.root._w, imgicon)
        
        self.root.mainloop()


def main():
    
    mainLoop = runMainloop()
    
    # Link Ctrl+C keystroke in shell to terminating window
    signal(SIGINT, lambda signal, frame, obj=mainLoop, root=None, skipUpdate=False: sigintHandler(signal, obj, root, skipUpdate))

    mainLoop.start()

if __name__ == '__main__':
    main()