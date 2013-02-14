class ApplicationController < ActionController::Base
  protect_from_forgery
  
  def licensing
    client = Mongo::Connection.new
    db = client['performance_platform']
    coll = db['licensing']
    results = coll.find.to_a
    results = results.map { |each| each.delete("_id"); each }
    
    render :json => results.to_json
  end
end
