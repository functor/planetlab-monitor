source("functions.r");

# system("./extract_all.py 2007-* > ../findbad_raw_2007.csv")
# system("./extract_all.py 2008-* > ../findbad_raw_2008.csv")
# system("./extract_all.py 2009-* > ../findbad_raw_2009.csv")

fb7 <- read.csv('findbad_raw_2007.csv', sep=',', header=TRUE)
fb8 <- read.csv('findbad_raw_2008.csv', sep=',', header=TRUE)
fb9 <- read.csv('findbad_raw_2009.csv', sep=',', header=TRUE)

online_nodes <- function (fb)
{
    breaks <- unique(fb$timestamp)
    n<-NULL
    o<-NULL
    x<-NULL
    for (i in seq(1,length(breaks)) )
    {
        ts <- breaks[i]
        sub <- fb[which(fb$timestamp == ts),]
        node_count   <- length(unique(sub$hostname))
        online_count <- length(unique(sub$hostname[which(sub$state=='BOOT')]))
        x<-c(x,ts)
        n<-c(n,node_count)
        o<-c(o,online_count)
    }
    print(length(x))
    print(length(n))
    print(length(o))
    return (rbind(x,n,o))
}
z7<- online_nodes(fb7)
z8<- online_nodes(fb8)
z9<- online_nodes(fb9)

plot(c(z7[1,],z8[1,],z9[1,]), log(c(z7[2,], z8[2,],z9[2,])), 
        ylim=c(0,7), xlim=c(min(x1), max(x1)), type='p', pch='.', axes=F)
points(c(z7[1,],z8[1,],z9[1,]) , log(c(z7[3,], z8[3,],z9[3,])), pch='.')



t_july08 <-unclass(as.POSIXct("2008-07-01", origin="1970-01-01"))[1]
breaks <- unique(fb8$timestamp[which(fb8$timestamp < t_july08)])
fb8_boot <- fb8$timestamp[which(fb8$state=="BOOT" & fb8$timestamp < t_july08)]
h8<-hist(fb8_boot, breaks=breaks[which(!is.na(breaks) & breaks!=0)])

breaks <- unique(as.numeric(as.character(fb9$timestamp)))
fb9_boot <- as.numeric(as.character(fb9$timestamp[which(fb9$state=="BOOT")]))
hist(fb9_boot, breaks=breaks[which(!is.na(breaks) & breaks >= 1230775020)])

