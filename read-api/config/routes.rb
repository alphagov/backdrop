ReadApi::Application.routes.draw do
  match "licensing" => "application#licensing", via: :get
end
