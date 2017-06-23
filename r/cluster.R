# Partition
#
# Greek
# "C:\Dev\R\R-3.3.2\bin\R.exe" --vanilla --args "C:\Data\Workspace\reading-processor\r\cluster-config.yml" "Mark 01-05 G" "C:\Data\Workspace\reading-processor\csv\c01-05G.csv" "C:\Data\Workspace\reading-processor\csv\c01-05SG.csv" "2" "G" < "C:\Data\Workspace\reading-processor\r\cluster.R" > out-g.txt
#
# Greek and Latin
# "C:\Dev\R\R-3.3.2\bin\R.exe" --vanilla --args "C:\Data\Workspace\reading-processor\r\cluster-config.yml" "Mark 01-05 GL" "C:\Data\Workspace\reading-processor\csv\c01-05GL.csv" "C:\Data\Workspace\reading-processor\csv\c01-05SG.csv" "3" "GL" < "C:\Data\Workspace\reading-processor\r\cluster.R" > out-gl.txt
#

require('Cairo')
require('cluster')
require('stringi')

# Similarity coefficients based on various methods
library('proxy') # for binary similarity coefficients
library('yaml')

CLUSTER_COLORS <- c('blue','darkturquoise','green3','deeppink','gold1','red')
WITNESS_COLORS = c('red','chartreuse3','darkgoldenrod3','turquoise4','coral2','green4','darkorchid4','blue3','darkred','springgreen4','violetred3','steelblue4','slateblue3','sienna3','tan3','tomato3','firebrick2','deepskyblue2','deeppink','royalblue3','lightsalmon3','mediumorchid3')

#####################################################################
#
# Function to compute and render clustered results
#
#####################################################################

computeResults <- function(dss, nclusters) {
  # Subdirectory for organization of clusters
  clustdir <- paste(outdir, sprintf("%i clusters", nclusters), sep="\\")
  if (!file.exists(clustdir)) {
    dir.create(clustdir);
  }

  # Subdirectory for output related to individual mss
  mssdir <- paste(clustdir, 'mss', sep="\\")
  if (!file.exists(mssdir)) {
    dir.create(mssdir);
  }

  # Switch out names since long names are desired for silhouette
  tempNames = row.names(dss)
  
  # Short names for silhouette
  row.names(dss) <- shortNames

  cl <- pam(dss, nclusters, diss=FALSE, metric='manhattan', keep.diss=TRUE)
  sil <- silhouette(cl)

  # Restore medium names
  row.names(dss) <- tempNames
  cl <- pam(dss, nclusters, diss=FALSE, metric='manhattan', keep.diss=TRUE)

  # Color-coded by cluster
  if (IS_BW) {
    # Without labels
    CairoPNG(file=paste(clustdir, sprintf("%s - %i clusters PAM (points) BW.png", label, nclusters), sep="\\"),width=1000,height=1000)
    plot(cl, which=1, labels=5, cex.txt=1, col.p=c('gray35'))
    dev.off()

    CairoPNG(file=paste(clustdir, sprintf("%s - %i clusters PAM BW.png", label, nclusters), sep="\\"),width=1000,height=1000)
    plot(cl, which=1, labels=2, cex.txt=1, col.p=c('gray35'))
  }
  else {
    CairoPNG(file=paste(clustdir, sprintf("%s - %i clusters PAM.png", label, nclusters), sep="\\"),width=1000,height=1000)
    plot(cl, which=1, labels=2, cex.txt=1, col.p=CLUSTER_COLORS[cl$clustering])
  }
  dev.off()

  # Graphical distribution of Latin witnesses among clusters (multiplots)
  if (IS_BW) {
    plotname <- "%s - %i clusters by Latin Witness BW.png"
  }
  else {
    plotname <- "%s - %i clusters by Latin Witness.png"
  }

  if (LATINS > 0) {
    for (i in 1:LATINS) {
      if (i %% LATINS == 1) {
        CairoPNG(file=paste(clustdir, sprintf(plotname, label, nclusters), sep="\\"),width=1000,height=1200)
        par(mfrow = c(3, 4))
      }
      if (IS_BW) {
        plot(cl, which=1, labels=4, lines=0, shade=FALSE, main="", xlab=colnames(inData)[i], ylab="", cex.lab=4, cex=c(2,3)[(inData+1)[,i]], plotchar=FALSE, col.p='gray35', pch=c(5,18)[(inData+1)[,i]])
      }
      else {
        plot(cl, which=1, labels=4, lines=0, shade=TRUE, main="", xlab=colnames(inData)[i], ylab="", cex.lab=4, cex=4, col.p=c('gray35','red')[(inData+1)[,i]])
      }
    }
    dev.off()
  }

  # Graphical distribution of Greek witnesses among clusters (multiplots)
  if (IS_BW) {
    plotname <- "%s - %i clusters by Greek Witness BW.png"
  }
  else {
    plotname <- "%s - %i clusters by Greek Witness.png"
  }
  for (i in LATINS+1:nwitnesses-LATINS) {
    if (i %% nwitnesses-LATINS == 1) {
      CairoPNG(file=paste(clustdir, sprintf(plotname, label, nclusters), sep="\\"),width=1500,height=1200)
      par(mfrow = c(4, 5))
    }
    if (IS_BW) {
      plot(cl, which=1, labels=4, lines=0, shade=FALSE, main="", xlab=colnames(inData)[i], ylab="", cex.lab=4, cex=c(2,3)[(inData+1)[,i]], plotchar=FALSE, col.p='gray35', pch=c(5,18)[(inData+1)[,i]])
    }
    else {
      plot(cl, which=1, labels=4, lines=0, shade=TRUE, main="", xlab=colnames(inData)[i], ylab="", cex.lab=4, cex=4, col.p=c('black','red')[(inData+1)[,i]])
    }
  }
  dev.off()

  # Plot of Greek Mainstream and Old Latin layers and Alexandrian base
  CairoPNG(file=paste(clustdir, sprintf("%s - %i clusters w layers.png", label, nclusters), sep="\\"),width=600,height=600)
  psymbols = c(1,18,4,17,0) # hollow circle, solid diamond, x, solid triangle, hollow square
  if (LANG_CODE == 'D') {
    psymbols = c(18,0,1,4,17) # solid diamond, hollow square, hollow circle, x, solid triangle
  }
  plot(cl, which=1, labels=4, lines=0, main=sprintf("Readings supported by key layers"), cex=2, plotchar=FALSE, col.p='black', pch=psymbols[nodeLayers])
  dev.off()

  CairoPNG(file=paste(clustdir, sprintf("%s - %i clusters w layers (letters).png", label, nclusters), sep="\\"),width=600,height=600)
  plot(cl, which=1, labels=4, lines=0, main=sprintf("Readings supported by key layers"), cex=2, plotchar=FALSE, col.p='black', pch=c('M','D','L')[nodeLayers])
  dev.off()

  clustmatch <- integer(0)
  cnames <- character(0)
  for (j in 1:nclusters){
    cnames <- c(cnames, c(sprintf("%i.C%i", nclusters, j)))
  }
  cnames <- c(cnames, c(sprintf("%i.SUM", nclusters)))
  for (i in 1:nwitnesses){
    # Graphical distribution of each witness per cluster
    if (IS_BW) {
      CairoPNG(file=paste(mssdir, sprintf("%s - %i clusters with %s BW.png", label, nclusters, colnames(inData)[i]), sep="\\"),width=600,height=600)
      plot(cl, which=1, labels=0, lines=0, main=sprintf("Readings supported by %s", colnames(inData)[i]), cex.txt=3, cex=c(1,2)[(inData+1)[,i]], plotchar=FALSE, col.p='gray35', pch=c(5,18)[(inData+1)[,i]])
    } else {
      CairoPNG(file=paste(mssdir, sprintf("%s - %i clusters with %s.png", label, nclusters, colnames(inData)[i]), sep="\\"),width=1000,height=1000)
      plot(cl, which=1, labels=2, cex.txt=1, col.p=c('black',WITNESS_COLORS[(i%%length(WITNESS_COLORS))+1])[(inData+1)[,i]])
    }
    dev.off()

    # How many times does current witness occur in current cluster?
    crow <- rep(0, nclusters+1)
    for (j in 1:nclusters){
      crow[j] <- length(which(cl$clustering[which(inData[,i]==1)]==j))
    }
    crow[nclusters+1] <- sum(crow[1:nclusters])
    clustmatch <- rbind(clustmatch, crow)
  }

  # TODO: Fix me!
  colnames(clustmatch) <- cnames
  #clusterMatches <- cbind(clusterMatches, clustmatch)

  clusters <- cl$clustering

  # Classic k-means (binary) results
  fileConn<-file(paste(clustdir, sprintf("%s - %i cluster results.txt", label, nclusters), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)

  for (i in 1:nclusters) {
    # display cluster
    cat('CLUSTER ', toString(i), '\n')
    cat(' Coord   Ly Nb Description\n')
    clSil <- sil[which(sil[,'cluster']==i),]
    for (j in 1:dim(clSil)[1]) {
      # display row
      shortName <- row.names(clSil)[j]
      obsIndex <- match(shortName, shortNames)
      longName <- fullNames[obsIndex]
      nodeLayer <- nodeLayers[obsIndex]
      width <- round(clSil[,'sil_width'], 4)[j]
      wstr <- toString(width)
      if (width >= 0) { cat(' ') } # for minus sign
      cat(wstr)
      strl <- stri_length(wstr)
      if (width < 0) { strl <- strl - 1 } # move one left for minus sign
      if (strl == 6) {
        cat('  ') }
      else if (strl == 7) { # neg sign
        cat('  ') }
      else if (strl == 5) {
        cat('   ') }
      else if (strl == 4) {
        cat('    ') }
      else if (strl == 3) {
        cat('     ') }
      else { 
        cat('    ') }
      cat(nodeLayer)
      cat('  ')
      cat(clSil[,'neighbor'][j])
      cat('  ')
      cat(longName)
      cat('\n')
    }
    cat('\n')
  }

  cat('\n\nCLUSTER INFO\n')
  print(cl$clusinfo)

  cat('\n\nCLUSTER ISOLATION\n')
  print(cl$isolation)

  cat('\n\nMEDOID OBSERVATIONS\n')
  medoidNames <- longNames[cl$id.med]
  cat('    Index Description\n')
  for (i in 1:length(medoidNames)) {
    cat('C')
    cat(toString(i))
    cat('  ')
    cat(cl$id.med[i])
    strl <- stri_length(toString(cl$id.med[i]))
    if (strl == 1) {
      cat('    ') }
    else if (strl == 2) {
      cat('   ') }
    else { # strl == 3
      cat('  ') }
    cat(medoidNames[i])
    cat('\n')
  }
  sink()
  close(fileConn)

  # Classic k-means (binary) results
  fileConn<-file(paste(clustdir, sprintf("%s-%icl-results.json", label, nclusters), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)
  cat('{\n')
  cat('  "languageCode": "')
  cat(LANG_CODE)
  cat('",\n')
  cat('  "clusters": [')
  for (i in 1:nclusters) {
    cat('  {\n') # cluster

    cat('    "index": "')
    cat(i)
    cat('",\n')

    cat('    "size": "')
    cat(cl$clusinfo[,1][i])
    cat('",\n')

    cat('    "max-diss": "')
    cat(round(cl$clusinfo[,2][i]))
    cat('",\n')

    cat('    "avg-diss": "')
    cat(round(cl$clusinfo[,3][i]))
    cat('",\n')

    cat('    "diameter": "')
    cat(round(cl$clusinfo[,4][i]))
    cat('",\n')

    cat('    "separation": "')
    cat(round(cl$clusinfo[,5][i]))
    cat('",\n')

    cat('    "witnesses": [\n')
    for (j in 1:nwitnesses) {
      cat('    {\n') # witness

      cat('      "id": "')
      cat(colnames(inData)[j])
      cat('",\n')

      cat('      "occurrences": "')
      cat(length(which(cl$clustering[which(inData[,j]==1)]==i)))
      cat('"\n')

      cat('    }') # witness
      if (j != nwitnesses) {
        cat(',')
      }
      cat('\n')
    }
    cat('    ],\n') # witnesses

    cat('    "readings": [\n')
    clSil <- sil[which(sil[,'cluster']==i),]
    for (j in 1:dim(clSil)[1]) {
      # display row
      shortName <- row.names(clSil)[j]
      obsIndex <- match(shortName, shortNames)
      longName <- fullNames[obsIndex]
      nodeLayer <- nodeLayers[obsIndex]
      width <- round(clSil[,'sil_width'], 4)[j]
      wstr <- toString(width)
      cat('    {\n') # reading
      cat('      "reference": "')
      cat(varRefs[obsIndex])
      cat('",\n')

      cat('      "sequence": "')
      cat(sequences[obsIndex])
      cat('",\n')

      cat('      "fit": "')
      cat(wstr)
      cat('",\n')

      cat('      "layer": "')
      cat(nodeLayer)
      cat('",\n')

      cat('      "neighbor": "')
      cat(clSil[,'neighbor'][j])
      cat('",\n')

      cat('      "witnesses": "')
      cat(witnessStrs[obsIndex])
      cat('",\n')

      cat('      "excerpt": "')
      cat(varExcerpts[obsIndex])
      cat('",\n')

      cat('      "description": "')
      cat(longName)
      cat('"\n')

      cat('    }') # reading
      if (j != dim(clSil)[1]) {
        cat(',')
      }
      cat('\n')
    }
    cat('    ]\n') # readings
    cat('  }') # cluster
    if (i != nclusters || (length(singularRefsLong) > 0 && LANG_CODE != 'D')) {
      cat(',')
    }
    cat('\n')
  }
  if (length(singularRefsLong) > 0 && LANG_CODE != 'D') {
    cat('  {\n') # cluster
    cat('    "index": "')
    cat(nclusters + 1)
    cat('",\n')

    cat('    "size": "')
    cat(as.character(length(singularRefsLong)))
    cat('",\n')

    cat('    "max-diss": "0",\n')
    cat('    "avg-diss": "0",\n')
    cat('    "diameter": "0",\n')
    cat('    "separation": "0",\n')
    cat('    "witnesses": [],\n')
    cat('    "readings": [\n')
    for (j in 1:length(singularRefsLong)) {
      cat('    {\n') # reading

      cat('      "reference": "')
      cat(singularRefs[j])
      cat('",\n')

      cat('      "sequence": "')
      cat(singularSequences[j])
      cat('",\n')

      cat('      "fit": "')
      cat('1.0')
      cat('",\n')

      cat('      "layer": "')
      cat('4')
      cat('",\n')

      cat('      "neighbor": "')
      cat('0')
      cat('",\n')

      cat('      "witnesses": "",\n')

      cat('      "excerpt": "')
      cat(singularExcerpts[j])
      cat('",\n')

      cat('      "description": "')
      cat(singularRefsLong[j])
      cat('"\n')

      cat('    }') # reading
      if (j != length(singularRefsLong)) {
        cat(',')
      }
      cat('\n')
    }
    cat('    ]\n') # readings
    cat('  }\n') # cluster
  }
  cat('  ]\n') # clusters:
  cat('}\n')
  sink()
  close(fileConn)
} # computeResults

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

# Read data
infile <- cmdArgs[6]

# Singular readings for charts
singularInfile <- cmdArgs[7]

NUM_CLUSTERS <- as.numeric(cmdArgs[8])
LANG_CODE <- cmdArgs[9]

# RConsole Debugging
# config <- yaml.load_file("C:\\Data\\Workspace\\reading-processor\\r\\cluster-config.yml")
# label <- "Mark 01-05 GL"
# infile <- "C:\\Data\\Workspace\\reading-processor\\csv\\c01-05GL.csv"
# singularInfile <- "C:\\Data\\Workspace\\reading-processor\\csv\\c01-05SG.csv"

# Black-white mode
IS_BW <- as.logical(config[['general']][['bw']])

# Create directory for current label if not exists
outdir <- paste(config$outdir, label, sep="")
if (!file.exists(outdir)) {
  dir.create(outdir);
}

# Read data
inFrame <- read.delim(file=toString(infile), strip.white=TRUE, encoding="UTF-8")

singFrame <- read.delim(file=toString(singularInfile), strip.white=TRUE, encoding="UTF-8")
singularRefs <- iconv(as.vector(singFrame[,1]), to="UTF-8")
singularRefsLong <- iconv(as.vector(singFrame[,3]), to="UTF-8")
singularExcerpts <- iconv(as.vector(singFrame[,4]), to="UTF-8")
singularSequences <- iconv(as.vector(singFrame[,5]), to="UTF-8")

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

varRefs <- iconv(as.vector(shortNames), to="UTF-8")
fullNames <- iconv(as.vector(longNames), to="UTF-8")
sequences <- iconv(as.vector(nodeIds), to="UTF-8")
witnessStrs <- iconv(as.vector(witness_strs), to="UTF-8")
varExcerpts <- iconv(as.vector(excerpts), to="UTF-8")

# exclude column metadata
inData <- data.matrix(frame=inFrame[,8:dim(inFrame)[2]])

rownames(inData) <- mediumNames

nwitnesses <- dim(inData)[2]

# How many Latin witnesses in data set?
LATINS <- sum(startsWith(colnames(inData), 'VL') == TRUE)
LATINS <- LATINS + sum(startsWith(colnames(inData), 'vg') == TRUE)
LATINS <- LATINS + sum(startsWith(colnames(inData), 'X19A') == TRUE)

#####################################################################
#
# BINARY - PARTITIONING AROUND MEDIOIDS
#
#####################################################################

# Kulczynski (1927) 1/2[a/(a + b) + a/(a + c)]
simmat <- as.matrix(simil(inData, by_rows=TRUE, method='Kulczynski2', diag=TRUE))

# Replace NA's in simmat
simFr <- as.data.frame(simmat)
simFr[is.na(simFr)] <- 1
dssKulczynski2 <- as.matrix(simFr)

# Results for different numbers of clusters
computeResults(dssKulczynski2, NUM_CLUSTERS)
