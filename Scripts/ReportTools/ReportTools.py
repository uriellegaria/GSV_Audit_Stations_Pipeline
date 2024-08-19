import os
import sys
import pathlib

from pylatex import Document as Document
from pylatex import Section as Section
from pylatex import Subsection as Subsection
from pylatex import Command as Command
from pylatex import Figure as Figure
from pylatex import SubFigure as SubFigure
from pylatex import Itemize as Itemize

from pylatex.utils import italic as Italic
from pylatex.utils import bold as Bold
from pylatex.utils import NoEscape as NoEscape
from pylatex.basic import NewPage
from pylatex.basic import NewLine
from pylatex import Command
from pylatex import Package


class ResultChunk:
    
    def __init__(self, title, path, caption, scale, observations):
        self.title = title
        self.path = path
        self.caption = caption
        self.scale = scale
        self.observations = observations


class ResultsChunk:

    def __init__(self, sectionTitle, figurePaths, subcaptions, scaleFactors, figureCaption, observations = [], introductoryText = ""):
        self.sectionTitle = sectionTitle
        self.figurePaths = figurePaths
        self.subcaptions = subcaptions
        self.scaleFactors = scaleFactors
        self.figureCaption = figureCaption
        self.observations = observations
        self.introductoryText = introductoryText


class ReportCreator:
    
    
    def __init__(self, title, author,date):
        
        self.title = title
        self.author = author
        self.doc = Document('basic')
        self.doc.packages.append(Package('hyperref'))
        self.doc.preamble.append(Command('title', title))
        self.doc.preamble.append(Command('author', author))
        self.doc.preamble.append(Command('date', date))
        self.doc.append(NoEscape(r'\maketitle'))
        self.doc.append(NoEscape(r'\tableofcontents'))
        self.doc.append(NoEscape(r'\clearpage'))
        

    
    def addResults(self, sectionTitle, figurePaths, subcaptions, scaleFactors, figureCaption, observations=[], introductoryText=""):
        self.doc.append(NoEscape(r'\clearpage'))
        with self.doc.create(Section(sectionTitle)):
            if introductoryText:
                self.doc.append(introductoryText)
                self.doc.append(NewLine())

            with self.doc.create(Figure(position='h!')) as resultFigure:
                resultFigure.append(Command('centering'))
                if(len(figurePaths) > 1):
                    for i in range(len(figurePaths)):
                        path = figurePaths[i]
                        subcaption = subcaptions[i]
                        scaleFactor = scaleFactors[i]

                        # Create a Subfigure within the Figure
                        with self.doc.create(SubFigure(position='c', width=NoEscape(f'{scaleFactor}\\textwidth'))) as subResult:
                            subResult.add_image(path, width=NoEscape(f'{scaleFactor}\\textwidth'))
                            subResult.add_caption(subcaption)

                        # Add line break to ensure vertical alignment
                        if i < len(figurePaths) - 1:
                            resultFigure.append(NoEscape(r'\par'))  # This ensures the next subfigure starts on a new line
                
                elif(len(figurePaths) == 1):
                    path = figurePaths[0]
                    scaleFactor = scaleFactors[0]
                    resultFigure.add_image(path, width = NoEscape(f'{scaleFactor}\\textwidth'))

                resultFigure.add_caption(figureCaption)

            if observations:
                with self.doc.create(Subsection("Observations")):
                    with self.doc.create(Itemize()) as itemize:
                        for observation in observations:
                            itemize.add_item(observation)
    




    
    def addResult(self, sectionTitle, figurePath, figureCaption, scaleFactor, observations):
        with self.doc.create(Section(sectionTitle)):
            self.doc.append(Bold("Result"))
            with self.doc.create(Figure(position='!htb')) as resultPic:
                resultPic.add_image(figurePath, width=NoEscape(str(scaleFactor)+"\\textwidth"))
                resultPic.add_caption(figureCaption)
            if(len(observations) > 0):
                with self.doc.create(Subsection("Observations")):
                    with self.doc.create(Itemize()) as itemize:
                        for i in range(0,len(observations)):
                            itemize.add_item(observations[i])

            self.doc.append(NewPage())
            
    
    def addResultFromChunk(self, chunk):
        self.addResult(chunk.title, chunk.path, chunk.caption, chunk.scale, chunk.observations)
    
    def addResultsFromChunk(self, resultsChunk):
        self.addResults(resultsChunk.sectionTitle, resultsChunk.figurePaths, resultsChunk.subcaptions, resultsChunk.scaleFactors, resultsChunk.figureCaption, resultsChunk.observations,resultsChunk.introductoryText)
    
    
    def export(self, parentPath, fileName):
        if(not os.path.exists(parentPath)):
            os.makedirs(parentPath)
        self.doc.generate_pdf(parentPath + "/"+fileName, clean_tex=False)