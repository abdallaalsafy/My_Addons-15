odoo.define('pos_auth_discount.PosAuthDiscount', function (require) {
    'use strict';
    const DiscountButton = require('pos_discount.DiscountButton');
    const core = require('web.core');
    const _t = core._t;
    const Registries = require('point_of_sale.Registries')
    const NumberBuffer = require('point_of_sale.NumberBuffer')

    const PosDiscountButton = (DiscountButton)=>
        class extends DiscountButton{
           async onClick() {
                var self = this;
                var usr_pass = await this.showPopup('NumberPopup',{
                isPassword:true,
                title: _t('Enter Password')
                });
                if (usr_pass['confirmed']){
                    if (usr_pass['payload'] == this.env.pos.config.disc_password){
                        NumberBuffer.reset();
                        var { confirmed, payload } = await this.showPopup('NumberPopup',{
                                title: this.env._t('Discount Percentage'),
                            });
                            if (confirmed) {
                                self.apply_discount(payload);
                            }
                    }
                    else{
                        await this.showPopup('ErrorPopup',{
                        title: _t('Error'),
                        body:_t('The password Incorrect')
                        });
                    }
                }
            }
        }
        Registries.Component.extend(DiscountButton,PosDiscountButton);
        return PosDiscountButton;
});
