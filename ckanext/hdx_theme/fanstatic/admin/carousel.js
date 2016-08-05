(function(){

    var Item = Backbone.Model.extend({
        defaults: {
            title: null,
            description: null,
            order: 0,
            id: null,
            graphic: null,
            url: null,
            embed: false,
            buttonText: null,
            newTab: false,
            //internal state
            graphic_upload_preview: null,
            tab_open: true
        },
        idAttribute: 'id',
        fileAttribute: 'graphic_upload',
        methodToURL: {
            'create': '/ckan-admin/carousel/update',
            'read': '/ckan-admin/carousel/read',
            'patch': '/ckan-admin/carousel/update',
            'update': '/ckan-admin/carousel/update',
            'delete': '/ckan-admin/carousel/delete'
        },

        sync: function(method, model, options) {
            // console.log('syncing resource with method: ' + method);
            options = options || {};
            options.emulateHTTP = true;

            options.url = model.methodToURL[method.toLowerCase()];

            if (_.contains(['read', 'update', 'patch'], method)) {
                options.url += model.id;
            } else if (method == 'delete') {
                options.data = JSON.stringify({id: model.id});
            }
            return Backbone.sync.apply(this, arguments);
        }
    });

    var ItemView = Backbone.View.extend({
        tagName: 'div',
        className: '',
        template: _.template($('#carousel-item-tpl').html()),
        events: {
            'change .form-control': 'onFieldEdit',
            'click .carousel-item-header .toggle-tab-state': 'onTabChange',
            'click .carousel-item-header .delete-item': 'onDelete'
        },
        initialize: function(){
            this.model.view = this;
        },
        render: function(){
            var template_data = _.clone(this.model.attributes);
            template_data.template_position = this.model.collection.indexOf(this.model);
            template_data.lower_case_format = template_data.format ? template_data.format.toLowerCase() : null;
            var html = this.template(template_data);

            this.$el.html(html);
            this.$el.find("select").select2();

            return this;
        },
        onFieldEdit: function(e) {
            var value = e.target.value;
            if (e.target.type === "file"){
                value = e.target.files[0];
                this.model.set('graphic_upload_preview', URL.createObjectURL(value));
            }
            this.model.set(e.target.name, value);
            this.render();
        },
        onTabChange: function(e){
            this.model.set('tab_open', !this.model.get('tab_open'));
            this.render();
            return false;
        },
        onDelete: function(e){
            var deletedItem = this.collection.remove(this.model);
            if (deletedItem.get("id")){ //pre-existing item
                this.collection.deletedItems.push(deletedItem);
            }
            return false;
        }
    });

    var ItemCollection = Backbone.Collection.extend({
        model: Item,
        comparator: 'order',

        initialize: function(){
            this.fetch();
            this.deletedItems = [];
        },
        parse: function (data) {
            console.log("PArse");
            return data.results;
        },
        save: function () {
            var promise = $.Deferred();
            promise.resolve();
            //delete the removed items
            console.log("DELETING: ");
            for (var i = 0; i < this.deletedItems.length; i++){
                var item = this.deletedItems[i];
                var deleteModel = function(){
                    return item.destroy(null, {formData: true});
                };
                promise = promise.then(deleteModel);
                console.log(JSON.stringify(item));
            }
            console.log("SAVING: ");
            //save remaining items
            for (i = 0; i < this.models.length; i++){
                var model = this.models[i];

                var saveModel = function(){
                    return model.save(null, {formData: true});
                };

                promise = promise.then(saveModel);

                console.log(JSON.stringify(model));
            }

            promise
                .then(function(){
                    alert("Save ok!");
                })
                .fail(function(){
                    alert("Couldn't save, please check logs!");
                })
        },
        sync: function () { return null; },
        fetch: function () { return null; }
    });

    var ItemCollectionView = Backbone.View.extend({
        el: '#carousel-item-collection',
        events: {
            'sort-updated': 'onSortOrderChanged'
        },
        initialize: function(){
            this.render();
            this.listenTo(this.collection, 'sync add remove reset', this.render);
        },
        render: function(){
            this.$el.empty();
            this.collection.each(function(item){
                this.addOne(item);
            }, this);
            return this;
        },
        addOne: function(item){
            var view = new ItemView({model: item, collection: this.collection});
            this.$el.append(view.render().el);
        },
        onSortOrderChanged: function() {
            this.collection.each(function(item, i){
                item.set({order: (item.view.$el.index() + 1)});
            });
            this.collection.sort();
            this.render();
        }
    });

    var CarouselConfigView = Backbone.View.extend({
        el: "#carousel-config-main",
        events: {
            'click #add-carousel-item': 'onNewItem',
            'click #save-carousel': 'onSave'
        },
        initialize: function(options){
            this.collection = new ItemCollection();
            this.listView = new ItemCollectionView({collection: this.collection});

            this._setupSortable();
        },
        onNewItem: function(e){
            console.log("Click");
            this.collection.add(new Item({order: (this.collection.length + 1)}));
            return false;
        },
        onSave: function (e){
            console.log('Save');
            this.collection.save();
            return false;
        },
        _setupSortable: function(){
            // Initialize drag n drop sorting
            Sortable.create(this.listView.el, {
                animation: 250,
                // handle: ".drag-handle",
                scroll: true,
                onUpdate: function (e){
                    this.listView.$el.trigger('sort-updated');
                }.bind(this)
            });
        }
    });

    this.app = new CarouselConfigView({});

})();