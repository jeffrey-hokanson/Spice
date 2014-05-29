function imd_plot(filename,startpush)
% imd_plot(filename,startpush) plots the sum of all parameters' intensites
% for each push, showing n (set to 1024) pushes at a time.
% startpush is an optional input
% to specify at what push number to start; it defaults to 0. with the
% figure as the current window, pressing the down arrow shifts to the next
% n pushes; pressing the up arrow shifts to the previous n pushes. pressing
% q closes the figure and calls fclose.
%
% By: Rachel Finck
% Provided to JMH 29 May 2014.
% NO DISTRIBUTE
sigma=3;
ls=-10:10;
gaussFilter=exp(-ls.^2./(2*sigma^2));
gaussFilter=gaussFilter./sum(gaussFilter);

freq=76.8; %kHz
time=0;
str=get_imd_xml(filename);
str=str(1:2:length(str));

pstart=strfind(str,'<ShortName>');
pend=strfind(str,'</ShortName>');
l=length('<ShortName>');
num_cols=length(pstart);
colnames=cell(1,num_cols);

for i=1:num_cols
    colnames{i}=str(pstart(i)+l:pend(i)-1);
end


num_rows=1024;
dt=num_rows/freq;


fig=figure('KeyPressFcn',@rain);
fid=fopen(filename,'r');

if nargin>2
    oldpush=floor(startpush/num_rows)*num_rows;  %
    startpos=oldpush*4*num_cols;  %4 because 2 columns for each param, 2 bytes per entry since 16-bit
    push=oldpush+num_rows-1;
else
    startpos=0;
    oldpush=0;
    push=num_rows-1;
end

fseek(fid,startpos,'bof');
data=plot_rain(oldpush,push);


    function rain(src,event)
        cla
        if strcmp(event.Key,'downarrow')
            oldpush=push+1;
            push=push+num_rows;
            data=plot_rain(oldpush,push);

            
        elseif strcmp(event.Key,'uparrow');
            current_pos=ftell(fid);
            offset=2*4*num_cols*num_rows;
            newpos=current_pos-offset;
            if newpos >= 0
            fseek(fid,-offset,0);  %move to where just started, and then back one more
            push=oldpush-1;
            oldpush=oldpush-num_rows;
            data=plot_rain(oldpush,push);
            end
        else
                        
            fclose(fid);
            close(fig)
            return;
        end
    end




    function intensity=plot_rain(p1,p2)
        x=fread(fid,[num_cols*2 num_rows],'uint16')';
        intensity=x(:,1:2:2*num_cols);
        pulse=x(:,2:2:2*num_cols); 
        
        summed_int=sum(intensity,2); %can substitute pulse (or dual) here
        dual_conv=conv(summed_int,gaussFilter,'same');
        pl=plot(p1:p2,summed_int,'color',[0.5 0.5 0.5]);
        hold on
        pl2=plot(p1:p2,dual_conv,'k');
        
       
        legend([pl pl2 ],{'summed intensity' 'convolved summed intensity'});

        ylabel('summed intensity')
        xlabel('push number')
        line([p1 p2],[200 200],'color',[0.7 0.7 0.7],'linestyle',':')
    end


end

function str=get_imd_xml(filename)
% str=get_imd_xml(filename) extracts the XML at the end of an IMD file with
% name filename. Note that since the IMD files are 16-bit, there is a blank
% character separating every two characters in the str. To get rid of
% these, just add str=str(1:2:end) at the end.

db=double('<ExperimentSchema');
db=[db; zeros(size(db))];
startstr=char(db(:))';

fid=fopen(filename,'r','l');
fseek(fid,-1024,'eof');
str=char(fread(fid,1024,'char')');

pos=-2048;

startpos=strfind(str(1:1024),startstr);

while isempty(startpos)
    fseek(fid,pos,'cof');
    
    str=[ char(fread(fid,1024,'char')') str];
    
    startpos=strfind(str(1:1024),startstr);

end
fclose(fid);

str=str(startpos:end);

end
