import React from 'react';
import { Icon, Menu, Container, Segment } from 'semantic-ui-react';
import ModelsList from './Component/Model.js';
import ExperimentsList from './Component/Experiment.js';


class App extends React.Component {
  state = { activeItem: 'models' }

  handleMenuItemClick = (e, {name}) => {
    this.setState({
      activeItem: name,
    });
  }

  render() {
    const state = this.state
    var content = null

    switch (state.activeItem) {
    case 'models':
      content = <ModelsList/>
      break
    case 'experiments':
      content = <ExperimentsList/>
      break
    default:
      content = null
      break
    }

    return ([
      <Segment inverted attached compact size='mini'>
        <Menu inverted text compact size='large'>
          <Menu.Item>
            <Icon name="lab" size="large"/>
          </Menu.Item>
          <Menu.Item
            name='models'
            active={state.activeItem === 'models'}
            content=<b>Models</b>
            onClick={this.handleMenuItemClick}/>
          <Menu.Item
            name='experiments'
            active={this.state.activeItem === 'experiments'}
            content=<b>Experiments</b>
            onClick={this.handleMenuItemClick}/>
        </Menu>
      </Segment>,
      <Container>
        <Segment vertical>{content}</Segment>
      </Container>
    ]);
  }
}


export default App;
