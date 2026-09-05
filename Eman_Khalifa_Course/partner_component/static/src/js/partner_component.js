/** @odoo-module **/

const { Component } = owl;
const { useState } = owl.hooks;
const FormRenderer = require("web.FormRenderer");
const { ComponentWrapper } = require("web.OwlCompatibility");

class PartnerSaleOrder extends Component {
    partner = useState({});
    constructor(self,partner){
        super();
        this.partner = partner;
    }
};

Object.assign(PartnerSaleOrder,{
    template:"partner_component.partner_component"
});

FormRenderer.include({
    async _renderView() {
        await this._super(...arguments);
        const partnerId = this.state.data.partner_id?.res_id;
        if (!partnerId) {
            return;
        }
        for(const element of this.el.querySelectorAll(".o_partner_order_summary")){
            this._rpc({
                model:"res.partner",
                method: "read",
                args: [[partnerId]]
            }).then(data => {(new ComponentWrapper(this,PartnerSaleOrder,useState(data[0]))).mount(element);});
        }}
});
