#
# Greek and Latin
# "C:\Dev\R\R-3.3.2\bin\R.exe" --vanilla --args "C:\Data\Workspace\reading-processor\r\cluster-config.yml" "Mark 01-05 GL" "C:\Data\Workspace\reading-processor\csv\c01-05GL.csv" < "C:\Data\Workspace\reading-processor\r\cormat.R" > out-gl.txt
#

require('Cairo')
library('proxy') # for binary similarity coefficients
library('yaml')

#####################################################################
#
# Function to compute and output correlations between binary variables
#
#####################################################################

computeCorrelations <- function(meth) {
  cormat <- as.matrix(simil(inData, by_rows=FALSE, method=meth, diag=TRUE))
  simmat <- as.matrix(simil(inData, by_rows=TRUE, method=meth, diag=TRUE))
  dssmat <- as.matrix(dist(inData, by_rows=TRUE, method=meth, diag=TRUE))

  # Replace NA's in simmat
  simFr <- as.data.frame(simmat)
  simFr[is.na(simFr)] <- 1
  simmat <- as.matrix(simFr)

  # Output correlation matrix between witnesses
  fileConn<-file(paste(outdir, sprintf("%s - witness correlation matrix (%s).txt", label, meth), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)
  cat(colnames(cormat))
  cat('\n')
  for (i in 1:length(cormat[,1])) {
    tmp <- cormat[i,]
    names(tmp) <- NULL
    cat(tmp)
    cat('\n')
  }
  sink()
  close(fileConn)

  # Output similarity matrix between readings
  fileConn<-file(paste(outdir, sprintf("%s - reading similarity matrix (%s).txt", label, meth), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)
  cat(colnames(simmat))
  cat('\n')
  for (i in 1:length(simmat[,1])) {
    tmp <- simmat[i,]
    names(tmp) <- NULL
    cat(tmp)
    cat('\n')
  }
  sink()
  close(fileConn)

  # Output dissimilarity matrix between readings
  fileConn<-file(paste(outdir, sprintf("%s - reading dissimilarity matrix (%s).txt", label, meth), sep="\\"))
  sink(fileConn, append=FALSE, split=TRUE)
  cat(colnames(dssmat))
  cat('\n')
  for (i in 1:length(dssmat[,1])) {
    tmp <- dssmat[i,]
    names(tmp) <- NULL
    cat(tmp)
    cat('\n')
  }
  sink()
  close(fileConn)
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

# Read data
infile <- cmdArgs[6]

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

# exclude column metadata
inData <- data.matrix(frame=inFrame[,8:dim(inFrame)[2]])

rownames(inData) <- mediumNames

#####################################################################
#
# NUMBER OF CLUSTERS - WITHIN GROUPS SUM OF SQUARES (Everitt & Hothorn (pg. 251))
#
# A plot of the within groups sum of squares by number of clusters extracted 
# can help determine the appropriate number of clusters. The analyst looks 
# for a bend in the plot similar to a scree test in factor analysis.
#
#####################################################################

# Determine number of clusters
wss <- (nrow(inData)-1)*sum(apply(inData,2,var))
for (i in 2:15) wss[i] <- sum(kmeans(inData, centers=i)$withinss)

CairoPNG(file=paste(outdir, sprintf("%s - Within groups sum of squares X Number of Clusters.png", label), sep="\\"),width=1000,height=1000)
plot(1:15, wss, type="b", xlab="Number of Clusters", ylab="Within groups sum of squares") 
dev.off()

#####################################################################
#
# BINARY - PARTITIONING AROUND MEDIOIDS
#
#####################################################################

# Distance (dissimilarity) matrix (between observations)
dssJacard <- as.matrix(dist(inData, method="binary"))

# Output distance matrix
fileConn<-file(paste(outdir, sprintf("%s - distance matrix.txt", label), sep="\\"))
sink(fileConn, append=FALSE, split=TRUE)
cat(colnames(dssJacard))
cat('\n')
for (i in 1:length(dssJacard[,1])) {
  tmp <- dssJacard[i,]
  names(tmp) <- NULL
  cat(tmp)
  cat('\n')
}
sink()
close(fileConn)

# Determine number of clusters using Jacard indices
wss <- (nrow(dssJacard)-1)*sum(apply(dssJacard,2,var))
for (i in 2:15) wss[i] <- sum(kmeans(dssJacard, centers=i)$withinss)

CairoPNG(file=paste(outdir, sprintf("%s - Binary within groups sum of squares X Number of Clusters.png", label), sep="\\"),width=1000,height=1000)
plot(1:15, wss, type="b", xlab="Number of Clusters", ylab="Within groups sum of squares") 
dev.off()

dssKulczynski2 <- computeCorrelations('Kulczynski2')
