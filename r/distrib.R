# Greek and Latin
# "C:\Dev\R\R-3.3.2\bin\R.exe" --vanilla --args "C:\Data\Workspace\reading-processor\r\cluster-config.yml" "Mark 01-05GL" "Mark 1" "C:\Data\Workspace\reading-processor\csv\c01-05GL.csv" "C:\Data\Workspace\reading-processor\csv\c01-05SG.csv" < "C:\Data\Workspace\reading-processor\r\distrib.R" > out-gl.txt
#

require('Cairo')
require('stringi')

# Similarity coefficients based on various methods
library('yaml')

# Summary stats and charts
library('Hmisc')
library('pastecs')
library('psych')
library('UsingR')

COLOR_SCHEMES <- list()

grays <- list()
grays[[1]] <- c("#f0f0f0")
grays[[2]] <- c("#f0f0f0","#bdbdbd")
grays[[3]] <- c("#f0f0f0","#bdbdbd","#636363")
grays[[4]] <- c("#f7f7f7","#cccccc","#969696","#525252")
grays[[5]] <- c("#f7f7f7","#cccccc","#969696","#636363","#252525")
grays[[6]] <- c("#f7f7f7","#d9d9d9","#bdbdbd","#969696","#636363","#252525")
grays[[7]] <- c("#f7f7f7","#d9d9d9","#bdbdbd","#969696","#737373","#525252","#252525")
grays[[8]] <- c("#ffffff","#f0f0f0","#d9d9d9","#bdbdbd","#969696","#737373","#525252","#252525")
grays[[9]] <- c("#ffffff","#f0f0f0","#d9d9d9","#bdbdbd","#969696","#737373","#525252","#252525","#000000")

COLOR_SCHEMES[["grays"]] <- grays

reds <- list()
reds[[1]] <- c("#ffeda0")
reds[[2]] <- c("#ffeda0","#feb24c")
reds[[3]] <- c("#ffeda0","#feb24c","#f03b20")
reds[[4]] <- c("#ffffb2","#fecc5c","#fd8d3c","#e31a1c")
reds[[5]] <- c("#ffffb2","#fecc5c","#fd8d3c","#f03b20","#bd0026")
reds[[6]] <- c("#ffffb2","#fed976","#feb24c","#fd8d3c","#f03b20","#bd0026")
reds[[7]] <- c("#ffffb2","#fed976","#feb24c","#fd8d3c","#fc4e2a","#e31a1c","#b10026")
reds[[8]] <- c("#ffffcc","#ffeda0","#fed976","#feb24c", "#fd8d3c","#fc4e2a","#e31a1c","#b10026")
reds[[9]] <- c("#ffffcc","#ffeda0","#fed976","#feb24c","#fd8d3c","#fc4e2a","#e31a1c","#bd0026","#800026")

COLOR_SCHEMES[["reds"]] <- reds

greens <- list()
greens[[1]] <- c("#f7fcb9")
greens[[2]] <- c("#f7fcb9","#addd8e")
greens[[3]] <- c("#f7fcb9","#addd8e","#31a354")
greens[[4]] <- c("#ffffcc","#c2e699","#78c679","#238443")
greens[[5]] <- c("#ffffcc","#c2e699","#78c679","#31a354","#006837")
greens[[6]] <- c("#ffffcc","#d9f0a3","#addd8e","#78c679","#31a354","#006837")
greens[[7]] <- c("#ffffcc","#d9f0a3","#addd8e","#78c679","#41ab5d","#238443","#005a32")
greens[[8]] <- c("#ffffe5","#f7fcb9","#d9f0a3","#addd8e","#78c679","#41ab5d","#238443","#005a32")
greens[[9]] <- c("#ffffe5","#f7fcb9","#d9f0a3","#addd8e","#78c679","#41ab5d","#238443","#006837","#004529")

COLOR_SCHEMES[["greens"]] <- greens

aquas <- list()
aquas[[1]] <- c("#edf8b1")
aquas[[2]] <- c("#edf8b1","#7fcdbb")
aquas[[3]] <- c("#edf8b1","#7fcdbb","#2c7fb8")
aquas[[4]] <- c("#ffffcc","#a1dab4","#41b6c4","#225ea8")
aquas[[5]] <- c("#ffffcc","#a1dab4","#41b6c4","#2c7fb8","#253494")
aquas[[6]] <- c("#ffffcc","#c7e9b4","#7fcdbb","#41b6c4","#2c7fb8","#253494")
aquas[[7]] <- c("#ffffcc","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#0c2c84")
aquas[[8]] <- c("#ffffd9","#edf8b1","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#0c2c84")
aquas[[9]] <- c("#ffffd9","#edf8b1","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#253494","#081d58")

COLOR_SCHEMES[["aquas"]] <- aquas

purples <- list()
purples[[1]] <- c("#efedf5")
purples[[2]] <- c("#efedf5","#bcbddc")
purples[[3]] <- c("#efedf5","#bcbddc","#756bb1")
purples[[4]] <- c("#f2f0f7","#cbc9e2","#9e9ac8","#6a51a3")
purples[[5]] <- c("#f2f0f7","#cbc9e2","#9e9ac8","#756bb1","#54278f")
purples[[6]] <- c("#f2f0f7","#dadaeb","#bcbddc","#9e9ac8","#756bb1","#54278f")
purples[[7]] <- c("#f2f0f7","#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486")
purples[[8]] <- c("#fcfbfd","#efedf5","#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#4a1486")
purples[[9]] <- c("#fcfbfd","#efedf5","#dadaeb","#bcbddc","#9e9ac8","#807dba","#6a51a3","#54278f","#3f007d")

COLOR_SCHEMES[["purples"]] <- purples

magentas <- list()
magentas[[1]] <- c("#e7e1ef")
magentas[[2]] <- c("#e7e1ef","#c994c7")
magentas[[3]] <- c("#e7e1ef","#c994c7","#dd1c77")
magentas[[4]] <- c("#f1eef6","#d7b5d8","#df65b0","#ce1256")
magentas[[5]] <- c("#f1eef6","#d7b5d8","#df65b0","#dd1c77","#980043")
magentas[[6]] <- c("#f1eef6","#d4b9da","#c994c7","#df65b0","#dd1c77","#980043")
magentas[[7]] <- c("#f1eef6","#d4b9da","#c994c7","#df65b0","#e7298a","#ce1256","#91003f")
magentas[[8]] <- c("#f7f4f9","#e7e1ef","#d4b9da","#c994c7","#df65b0","#e7298a","#ce1256","#91003f")
magentas[[9]] <- c("#f7f4f9","#e7e1ef","#d4b9da","#c994c7","#df65b0","#e7298a","#ce1256","#980043","#67001f")

COLOR_SCHEMES[["magentas"]] <- magentas

#####################################################################
#
# Function for verse distribution plots
#
#####################################################################

verseHeatmaps <- function(colorName) {
  # verse representation by layer
  versesM <- as.numeric(versesPerUnit)[which(nodeLayers==1)]
  versesD <- as.numeric(versesPerUnit)[which(nodeLayers==2)]
  versesL <- as.numeric(versesPerUnit)[which(nodeLayers==3)]

  # occurrences per verse by layer
  tabM <- tabulate(versesM)
  tabD <- tabulate(versesD)
  tabL <- tabulate(versesL)
  tabAll <- tabulate(as.numeric(versesPerUnit))

  rangeM <- range(tabM)[2] - range(tabM)[1] + 1
  rangeD <- range(tabD)[2] - range(tabD)[1] + 1
  rangeL <- range(tabL)[2] - range(tabL)[1] + 1

  if (HAS_SING) {
    versesS <- as.numeric(versesPerUnitSing)
    tabS <- tabulate(versesS)
    rangeS <- range(tabS)[2] - range(tabS)[1] + 1
  }

  cScheme <- COLOR_SCHEMES[[colorName]]
  if (rangeM > length(cScheme)) {
    tabM <- floor(tabM * length(cScheme) / rangeM)
    rangeM <- range(tabM)[2] - range(tabM)[1] + 1
  }

  if (rangeD > length(cScheme)) {
    tabD <- floor(tabD * length(cScheme) / rangeD)
    rangeD <- range(tabD)[2] - range(tabD)[1] + 1
  }

  if (rangeL > length(cScheme)) {
    tabL <- floor(tabL * length(cScheme) / rangeL)
    rangeL <- range(tabL)[2] - range(tabL)[1] + 1
  }

  if (HAS_SING) {
    if (rangeS > length(cScheme)) {
      tabS <- floor(tabS * length(cScheme) / rangeS)
      rangeS <- range(tabS)[2] - range(tabS)[1] + 1
    }
  }

  # Subdirectory for charts showing occurrences per verse by layer
  versedistdir <- paste(outdir, 'verse-distrib', sep="\\")
  if (!file.exists(versedistdir)) {
    dir.create(versedistdir);
  }

  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer verse heatmap - %s.png", label, colorName), sep="\\"),width=800,height=500)
  par(mfrow = c(4, 1))
  verseHeatmap(tabM, rangeM, "M Layer", colorName)
  verseHeatmap(tabD, rangeD, "D Layer", colorName)
  verseHeatmap(tabL, rangeL, "L Layer", colorName)
  if (HAS_SING) {
    verseHeatmap(tabS, rangeS, "S Layer", colorName)
  }
  dev.off()

  # bar charts
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer verse barchart - %s.png", label, colorName), sep="\\"),width=800,height=600)
  par(mfrow = c(4, 1))
  verseBarchart(tabM, rangeM, "M Layer", colorName)
  verseBarchart(tabD, rangeD, "D Layer", colorName)
  verseBarchart(tabL, rangeL, "L Layer", colorName)
  if (HAS_SING) {
    verseBarchart(tabS, rangeS, "S Layer", colorName)
  }
  dev.off()

  # kernal density plots
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer kernel density BW.png", label), sep="\\"),width=800,height=800)
  par(mfrow = c(4, 1))
  densityPlot(tabM, "M Layer", "gray75")
  densityPlot(tabD, "D Layer", "gray75")
  densityPlot(tabL, "L Layer", "gray75")
  if (HAS_SING) {
    densityPlot(tabS, "S Layer", "gray75")
  }
  dev.off()

  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer kernel density.png", label), sep="\\"),width=800,height=800)
  par(mfrow = c(4, 1))
  densityPlot(tabM, "M Layer", "red")
  densityPlot(tabD, "D Layer", "red")
  densityPlot(tabL, "L Layer", "red")
  if (HAS_SING) {
    densityPlot(tabS, "S Layer", "red")
  }
  dev.off()

  # histograms
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer histograms BW.png", label), sep="\\"),width=800,height=800)
  par(mfrow = c(2, 2))
  hist(tabM, main=paste(PLOT_TITLE, "M Layer", sep=" - "), col="gray75")
  hist(tabD, main=paste(PLOT_TITLE, "D Layer", sep=" - "), col="gray75")
  hist(tabL, main=paste(PLOT_TITLE, "L Layer", sep=" - "), col="gray75")
  if (HAS_SING) {
    hist(tabS, main=paste(PLOT_TITLE, "S Layer", sep=" - "), col="gray75")
  }
  dev.off()

  # histograms
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer histograms.png", label), sep="\\"),width=800,height=800)
  par(mfrow = c(2, 2))
  hist(tabM, main=paste(PLOT_TITLE, "M Layer", sep=" - "),col="red")
  hist(tabD, main=paste(PLOT_TITLE, "D Layer", sep=" - "),col="red")
  hist(tabL, main=paste(PLOT_TITLE, "L Layer", sep=" - "),col="red")
  if (HAS_SING) {
    hist(tabS, main=paste(PLOT_TITLE, "S Layer", sep=" - "),col="red")
  }
  dev.off()

  # strip charts
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer strip charts.png", label), sep="\\"),width=600,height=600)
  par(mfrow = c(2, 2))
  stripchart(tabM, main=paste(PLOT_TITLE, "M Layer", sep=" - "), method="stack")
  stripchart(tabD, main=paste(PLOT_TITLE, "D Layer", sep=" - "), method="stack")
  stripchart(tabL, main=paste(PLOT_TITLE, "L Layer", sep=" - "), method="stack")
  if (HAS_SING) {
    stripchart(tabS, main=paste(PLOT_TITLE, "S Layer", sep=" - "), method="stack")
  }
  dev.off()

  # dot plots
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer dot plots.png", label), sep="\\"),width=600,height=600)
  par(mfrow = c(2, 2))
  DOTplot(tabM, main=paste(PLOT_TITLE, "M Layer", sep=" - "))
  DOTplot(tabD, main=paste(PLOT_TITLE, "D Layer", sep=" - "))
  DOTplot(tabL, main=paste(PLOT_TITLE, "L Layer", sep=" - "))
  if (HAS_SING) {
    DOTplot(tabS, main=paste(PLOT_TITLE, "S Layer", sep=" - "))
  }
  dev.off()

  # box plots
  CairoPNG(file=paste(versedistdir, sprintf("%s - per layer box plots.png", label), sep="\\"),width=800,height=800)
  par(mfrow = c(2, 2))
  boxplot(tabM, main=paste(PLOT_TITLE, "M Layer", sep=" - "), horizontal=TRUE)
  boxplot(tabD, main=paste(PLOT_TITLE, "D Layer", sep=" - "), horizontal=TRUE)
  boxplot(tabL, main=paste(PLOT_TITLE, "L Layer", sep=" - "), horizontal=TRUE)
  if (HAS_SING) {
    boxplot(tabS, main=paste(PLOT_TITLE, "S Layer", sep=" - "), horizontal=TRUE)
  }
  dev.off()

  # Data summary
  fileConn<-file(paste(versedistdir, sprintf("%s - distribution data summary.txt", label), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)
  cat('Data Summary\n')
  cat('M Layer - 5 num: ')
  cat(fivenum(tabM))
  cat('\n')
  print(psych::describe(tabM))
  print(stat.desc(tabM))
  print(summary(tabM))

  cat('\nD Layer - 5 num: ')
  cat(fivenum(tabD))
  cat('\n')
  print(psych::describe(tabD))
  print(stat.desc(tabD))
  print(summary(tabD))

  cat('\nL Layer - 5 num: ')
  cat(fivenum(tabL))
  cat('\n')
  print(psych::describe(tabL))
  print(stat.desc(tabL))
  print(summary(tabL))

  if (HAS_SING) {
    cat('\nS Layer - 5 num: ')
    cat(fivenum(tabS))
    cat('\n')
    print(psych::describe(tabS))
    print(stat.desc(tabS))
    print(summary(tabS))
    cat('\n')
  }


  cat('\nDescription - Hmisc.describe()\n')
  cat('M Layer\n')
  print(Hmisc::describe(tabM))
  cat('\n')

  cat('\nD Layer\n')
  print(Hmisc::describe(tabD))
  cat('\n')

  cat('\nL Layer\n')
  print(Hmisc::describe(tabL))
  cat('\n')

  if (HAS_SING) {
    cat('\nS Layer\n')
    print(Hmisc::describe(tabS))
    cat('\n')
  }


  cat('\nQuantiles\n')
  cat('M Layer\n')
  print(quantile(tabM))

  cat('D Layer\n')
  print(quantile(tabD))

  cat('L Layer\n')
  print(quantile(tabL))

  if (HAS_SING) {
    cat('S Layer\n')
    print(quantile(tabS))
    cat('\n')
  }


  cat('\nM Layer Density')
  print(density(tabM))

  cat('\n\nD Layer Density')
  print(density(tabD))

  cat('\n\nL Layer Density')
  print(density(tabL))

  if (HAS_SING) {
    cat('\n\nS Layer Density')
    print(density(tabS))
    cat('\n')
  }


  cat('\nLayer Occurrence per Verse\n')
  cat('M Layer\n')
  print(table(versesM))
  cat('\n')

  cat('D Layer\n')
  print(table(versesD))
  cat('\n')

  cat('L Layer\n')
  print(table(versesL))
  cat('\n')

  if (HAS_SING) {
    cat('S Layer\n')
    print(table(versesS))
    cat('\n')
  }


  cat('\nStem Charts\n')
  cat('M Layer\n')
  cat(stem(tabM))
  cat('\n')

  cat('D Layer\n')
  cat(stem(tabD))
  cat('\n')

  cat('L Layer\n')
  cat(stem(tabL))
  cat('\n')

  if (HAS_SING) {
    cat('S Layer\n')
    cat(stem(tabS))
    cat('\n')
  }


  cat('\nDistribution of Layer Occurrences per Verse\n')
  cat('M Layer\n')
  cat(tabM)
  cat('\n\n')

  cat('D Layer\n')
  cat(tabD)
  cat('\n\n')

  cat('L Layer\n')
  cat(tabL)
  cat('\n\n')

  if (HAS_SING) {
    cat('S Layer\n')
    cat(tabS)
    cat('\n\n')
  }

  sink()
  close(fileConn)
}

#####################################################################
#
# Function for individual verse density plots
#
#####################################################################

densityPlot <- function(vect, layerName, colorName) {
  d <- density(vect)
  plot(d, main=paste(PLOT_TITLE, layerName, sep=" - "))
  polygon(d, col=colorName, border=colorName)
}

#####################################################################
#
# Function for individual verse bar charts
#
#####################################################################

verseBarchart <- function(vect, vectRange, layerName, colorName) {
  cScheme <- COLOR_SCHEMES[[colorName]]
  par(lty = 0)
  if (vectRange > length(cScheme)) {
    vect <- floor(vect * length(cScheme) / vectRange)
    vectRange = length(cScheme)
  }
  barplot(vect, col=cScheme[[vectRange]][vect + 1], ylim=c(0,vectRange), axes=FALSE, names.arg=as.character(seq(1,length(vect),1)))
  title(main=paste(PLOT_TITLE, layerName, sep=" - "))
}

#####################################################################
#
# Function for individual verse heatmap plots
#
#####################################################################

verseHeatmap <- function(vect, vectRange, layerName, colorName) {
  cScheme <- COLOR_SCHEMES[[colorName]]
  if (vectRange > length(cScheme)) {
    vect <- floor(vect * length(cScheme) / vectRange)
    vectRange = length(cScheme)
  }
  image(matrix(vect),col=cScheme[[vectRange]], axes=FALSE)
  labs <- as.character(seq(1,length(vect),1))
  axis(1,labels=labs,at=seq(0,1,1/(length(vect)-1)))
  title(main=paste(PLOT_TITLE, layerName, sep=" - "))
}

#####################################################################
#
# Start script Execution
#
#####################################################################

options(max.print=5E5, echo = FALSE)

# Script logic
cmdArgs <- commandArgs()

config <- yaml.load_file(cmdArgs[4])

label <- cmdArgs[5]
PLOT_TITLE <- cmdArgs[6]

# Read data
infile <- cmdArgs[7]

# Singular readings for charts
singularInfile <- cmdArgs[8]

# Create directory for current label if not exists
outdir <- paste(config$outdir, label, sep="")
if (!file.exists(outdir)) {
  dir.create(outdir);
}

# Read data
inFrame <- read.delim(file=toString(infile), strip.white=TRUE, encoding="UTF-8")


#####################################################################
#
# Extract short, medium, and long row names from data
#
#####################################################################

shortNames <- inFrame[,1]
mediumNames <- inFrame[,2]
longNames <- inFrame[,3]
nodeIds <- inFrame[,4]
nodeLayers <- inFrame[,5]
witness_strs <- inFrame[,6]
excerpts <- inFrame[,7]

# Extract vector of verses for each variation unit
splitNames <- strsplit(as.character(shortNames), c('\\.'))

# Keep first two cols
for (i in 1:length(splitNames)) {
  subvect <- splitNames[[i]]
  if (length(subvect) > 2) {
    splitNames[[i]] <- head(subvect, 2)
  }
}

# Extract verses column of references split on '.'
versesPerUnit <- matrix(unlist(splitNames), ncol=2, byrow=TRUE)[,1]

# exclude column metadata
inData <- data.matrix(frame=inFrame[,8:dim(inFrame)[2]])

# partition by layer
layerL <- inData[which(nodeLayers==3),]
layerD <- inData[which(nodeLayers==2),]
layerM <- inData[which(nodeLayers==1),]

rownames(inData) <- mediumNames

nwitnesses <- dim(inData)[2]

# Distribution of layers

# singular readings
singFrame <- read.delim(file=toString(singularInfile), strip.white=TRUE, encoding="UTF-8")
singularRefs <- singFrame[,1]
HAS_SING = TRUE
if (length(singularRefs) == 0) {
  HAS_SING = FALSE
}
if (HAS_SING) {
  splitNamesSing <- strsplit(as.character(singularRefs), c('\\.'))
  versesPerUnitSing <- matrix(unlist(splitNamesSing), ncol=2, byrow=TRUE)[,1]
}

# Subdirectory for charts showing distribution of layers
layerdir <- paste(outdir, 'layer-distrib', sep="\\")
if (!file.exists(layerdir)) {
  dir.create(layerdir);
}

# grayscale
CairoPNG(file=paste(layerdir, sprintf("%s - layer distribution 800 BW.png", label), sep="\\"),width=800,height=175)
image(matrix(nodeLayers), col=c("#f0f0f0","#bdbdbd","#636363"), axes=FALSE)
labs <- versesPerUnit[seq(1,length(versesPerUnit),5)]
axis(1,labels=labs,at=seq(0,1,1/(length(labs)-1)))
title(main=paste("", PLOT_TITLE))
dev.off()

# green
CairoPNG(file=paste(layerdir, sprintf("%s - layer distribution 800 green.png", label), sep="\\"),width=800,height=175)
image(matrix(nodeLayers), col=c("#ffffbf","#a6d96a","#1a9641"), axes=FALSE)
labs <- versesPerUnit[seq(1,length(versesPerUnit),5)]
axis(1,labels=labs,at=seq(0,1,1/(length(labs)-1)))
title(main=paste("", PLOT_TITLE))
dev.off()

# occurrences per verse by layer
verseHeatmaps("grays")
verseHeatmaps("reds")
verseHeatmaps("greens")
verseHeatmaps("magentas")


# Subdirectory for charts showing distribution of distinctive agreements
distinctivedir <- paste(outdir, 'distinctive-distrib', sep="\\")
if (!file.exists(distinctivedir)) {
  dir.create(distinctivedir);
}

# Distribution of distinctive agreements per witness
for (i in 1:nwitnesses){
  distinctive_vect <- 9 - rowSums(inData) + 1
  distinctive_vect[which(distinctive_vect < 0)] <- 0
  distinctive_vect <- inData[,i] * distinctive_vect

  CairoPNG(file=paste(distinctivedir, sprintf("%s - distinctive agreements with %s BW.png", label, colnames(inData)[i]), sep="\\"),width=1600,height=300)
  par(lty = 0)
  barplot(distinctive_vect, col="gray60", ylim=c(0,9), axes=FALSE, names.arg=versesPerUnit)
  title(main=colnames(inData)[i], cex.main=2)
  dev.off()

  CairoPNG(file=paste(distinctivedir, sprintf("%s - distinctive agreements with %s.png", label, colnames(inData)[i]), sep="\\"),width=1600,height=300)
  par(lty = 0)
  barplot(distinctive_vect, col=magentas[[9]][distinctive_vect + 1], ylim=c(0,9), axes=FALSE, names.arg=versesPerUnit)
  title(main=colnames(inData)[i], cex.main=2)
  dev.off()
}

# Distribution of distinctive agreements per witness multi-plot

# grayscale
CairoPNG(file=paste(distinctivedir, sprintf("%s - distinctive agreements by witness.png", label), sep="\\"),width=2000,height=2000)
par(mfrow = c(14, 2))
par(lty = 0)
par(cex.axis = 2)
par(cex.lab = 2)
for (i in 1:nwitnesses){
  distinctive_vect <- 9 - rowSums(inData) + 1
  distinctive_vect[which(distinctive_vect < 0)] <- 0
  distinctive_vect <- inData[,i] * distinctive_vect
  barplot(distinctive_vect, col="gray60", ylim=c(0,9), axes=FALSE, names.arg=versesPerUnit)
  title(sub=colnames(inData)[i], cex.sub=3)
}
dev.off()

# red
CairoPNG(file=paste(distinctivedir, sprintf("%s - distinctive agreements by witness (red).png", label), sep="\\"),width=2000,height=2000)
par(mfrow = c(14, 2))
par(lty = 0)
par(cex.axis = 2)
par(cex.lab = 2)
for (i in 1:nwitnesses){
  distinctive_vect <- 9 - rowSums(inData) + 1
  distinctive_vect[which(distinctive_vect < 0)] <- 0
  distinctive_vect <- inData[,i] * distinctive_vect
  barplot(distinctive_vect, col="red", ylim=c(0,9), axes=FALSE, names.arg=versesPerUnit)
  title(sub=colnames(inData)[i], cex.sub=3)
}
dev.off()
