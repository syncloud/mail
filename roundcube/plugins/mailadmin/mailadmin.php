<?php

class mailadmin extends rcube_plugin
{
    public $noajax = true;

    function init()
    {
        $url = rcmail::get_instance()->config->get('mailadmin_url');
        if (empty($url)) {
            return;
        }

        $this->add_texts('localization/', false);
        $this->include_stylesheet($this->local_skin_path() . '/mailadmin.css');

        $this->add_button([
            'type'       => 'link',
            'label'      => 'mailadmin.admin',
            'title'      => 'mailadmin.admin',
            'href'       => $url,
            'class'      => 'button-mailadmin',
            'classsel'   => 'button-mailadmin button-selected',
            'innerclass' => 'button-inner',
        ], 'taskbar');

        $this->api->output->add_footer(
            '<script>document.addEventListener("DOMContentLoaded",function(){' .
            'var u=' . json_encode($url) . ';' .
            'var a=document.querySelector("#taskmenu a.button-mailadmin");' .
            'if(a){a.setAttribute("href",u);a.setAttribute("data-testid","nav-admin");' .
            'a.addEventListener("click",function(e){e.stopPropagation();e.preventDefault();window.location.assign(u);});}});</script>'
        );
    }
}
